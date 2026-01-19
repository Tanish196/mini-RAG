from dataclasses import dataclass
from time import perf_counter


@dataclass
class Timer:
	start_time: float
	end_time: float | None = None

	@property
	def elapsed_ms(self) -> float:
		end = self.end_time or perf_counter()
		return (end - self.start_time) * 1000


class time_block:
	def __enter__(self) -> Timer:
		self._timer = Timer(start_time=perf_counter())
		return self._timer

	def __exit__(self, exc_type, exc_val, exc_tb) -> None:
		self._timer.end_time = perf_counter()
