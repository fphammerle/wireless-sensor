import datetime

import wireless_sensor

# pylint: disable=protected-access


def test__now_local():
    now_local = wireless_sensor._now_local()
    assert (
        datetime.datetime.now(tz=datetime.timezone.utc) - now_local
    ).total_seconds() < 1
    assert now_local.tzinfo
