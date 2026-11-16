from datetime import datetime, timedelta, timezone
from statistics import mean
from mindsync.contracts import HistorySummary, Mode

class SQLiteContextProvider:
    def __init__(self, repository, stale_minutes=120, clock=None):
        self.repository = repository
        self.stale_minutes = stale_minutes
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def get_current_vitals(self, profile_id):
        now = self.clock()
        latest = self.repository.latest(profile_id, now)
        if latest and now-latest.measured_at <= timedelta(minutes=self.stale_minutes):
            return latest.model_copy(update={"simulated": True})
        return None

    def get_history_summary(self, profile_id, days=7):
        if not 1 <= days <= 30:
            raise ValueError("days must be between 1 and 30")
        now = self.clock()
        rows = self.repository.samples(profile_id, now-timedelta(days=days), now)
        sleep = self.repository.sleep(profile_id, (now-timedelta(days=days)).date(), now.date())
        midpoint = (now-timedelta(days=min(3, days))).date().isoformat()
        earlier = [r["hours"] for r in sleep if r["sleep_date"] < midpoint and r["hours"] is not None]
        recent = [r["hours"] for r in sleep if r["sleep_date"] >= midpoint and r["hours"] is not None]
        hr = [r.heart_rate_bpm for r in rows if r.heart_rate_bpm is not None]
        # Coverage uses hourly bins, so high-frequency publishing cannot hide gaps.
        bins = {}
        fields = ("heart_rate_bpm", "spo2_percent", "respiratory_rate_per_min", "activity_level")
        for row in rows:
            slot = int((now-row.measured_at).total_seconds() // 3600)
            if 0 <= slot < days*24:
                bins.setdefault(slot, set()).update(f for f in fields if getattr(row, f) is not None)
        coverage = sum(len(present) for present in bins.values()) / (days*24*4)
        return HistorySummary(profile_id=profile_id, window_days=days, sample_count=len(rows),
            mean_heart_rate_bpm=mean(hr) if hr else None,
            earlier_sleep_avg_hours=mean(earlier) if earlier else None,
            recent_sleep_avg_hours=mean(recent) if recent else None,
            missing_fraction=1-coverage, data_stale=self.get_current_vitals(profile_id) is None)

class RestrictedContextProvider:
    """Request-scoped capability boundary; never pass the raw provider to an agent."""
    def __init__(self, provider, request):
        self.__provider = provider
        self.__profile_id = request.profile_id
        self.__mode = request.mode
        self.__consent = request.consent_to_use_vitals

    def _allow(self, profile_id, history=False):
        if profile_id != self.__profile_id or not self.__consent or self.__mode == Mode.TEXT_ONLY or (history and self.__mode != Mode.FULL_CONTEXT):
            raise PermissionError("Context access is not permitted for this request")

    def get_current_vitals(self, profile_id):
        self._allow(profile_id)
        return self.__provider.get_current_vitals(profile_id)

    def get_history_summary(self, profile_id, days=7):
        self._allow(profile_id, history=True)
        return self.__provider.get_history_summary(profile_id, days)
