"""
tests/load/locustfile.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Locust load test entry point.

Usage
-----
  # Start web UI
  locust -f tests/load/locustfile.py --host http://localhost:8000

  # Headless - 500 users, 10/s spawn, 5 minutes
  locust -f tests/load/locustfile.py --host http://localhost:8000 \
    --headless -u 500 -r 10 -t 5m \
    --html tests/load/report.html

  # 10k concurrent (prod-like)
  locust -f tests/load/locustfile.py --host https://api.qommunity.app \
    --headless -u 10000 -r 100 -t 10m

User mix (weights reflect real traffic distribution):
  70%  RegularUser      - browse feed, view posts, like, comment
  20%  ContentCreator   - create posts frequently
  10%  PassiveUser      - notifications + profile only
"""

from locust import between, events

from tests.load.scenarios.feed import FeedScenario
from tests.load.scenarios.notifications import NotificationsScenario
from tests.load.scenarios.posts import PostsScenario


class RegularUser(FeedScenario, PostsScenario, NotificationsScenario):
    """Simulates a typical active community member."""

    weight = 70
    wait_time = between(1, 4)


class ContentCreator(PostsScenario, FeedScenario):
    """Simulates a power user who posts frequently."""

    weight = 20
    wait_time = between(0.5, 2)


class PassiveUser(NotificationsScenario, FeedScenario):
    """Simulates a user who mostly reads."""

    weight = 10
    wait_time = between(3, 8)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(
        "\n🏳️‍🌈  Qommunity Load Test Starting\n"
        f"   Target: {environment.host}\n"
        f"   Users:  {environment.parsed_options.num_users}\n"
    )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    print(
        f"\n📊  Load Test Complete\n"
        f"   Requests:       {stats.num_requests}\n"
        f"   Failures:       {stats.num_failures}\n"
        f"   Avg latency:    {stats.avg_response_time:.0f}ms\n"
        f"   P95 latency:    {stats.get_response_time_percentile(0.95):.0f}ms\n"
        f"   P99 latency:    {stats.get_response_time_percentile(0.99):.0f}ms\n"
        f"   Failure rate:   {stats.fail_ratio:.2%}\n"
    )
