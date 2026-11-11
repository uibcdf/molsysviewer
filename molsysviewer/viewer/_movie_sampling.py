"""Exact constant-rate, half-open sampling shared by Movie export owners."""

from fractions import Fraction
from numbers import Real


def frame_rate(value):
    if isinstance(value, bool) or not isinstance(value, (Real, str, Fraction)):
        raise ValueError("Movie fps must be a positive rate or a rational string such as '30000/1001'.")
    try:
        rate = Fraction(str(value))
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError("Movie fps must be a finite positive rate.") from error
    if not 0 < rate <= 240 or max(rate.numerator, rate.denominator) > 2**31 - 1:
        raise ValueError("Movie fps must be in (0, 240], with 32-bit rational components.")
    return rate


class _MovieSampling:
    def __init__(self, duration_ms, fps):
        self.rate = frame_rate(fps)
        self.duration = Fraction(str(duration_ms)) / 1000
        self.count = max(1, (self.duration * self.rate).__ceil__())
        if not 0 < self.duration or self.count > 2**53 - 1:
            raise ValueError("Movie export requires positive duration and a safely representable frame count.")

    def time_ms(self, index):
        if type(index) is not int or not 0 <= index < self.count:
            raise ValueError("Movie sample index is outside the export.")
        return float(Fraction(index * 1000, 1) / self.rate)

    def record(self):
        encoded = Fraction(self.count, 1) / self.rate
        return {
            "rule": "constant-rate-half-open@1",
            "fps": {"numerator": self.rate.numerator, "denominator": self.rate.denominator},
            "duration_ms": float(self.duration * 1000),
            "frame_count": self.count,
            "first_time_ms": 0.0,
            "last_time_ms": self.time_ms(self.count - 1),
            "encoded_duration_seconds": {"numerator": encoded.numerator, "denominator": encoded.denominator},
        }
