import datetime

import wireless_sensor

# pylint: disable=protected-access


def test__now_local():
    assert (
        datetime.datetime.now(tz=datetime.timezone.utc) - wireless_sensor._now_local()
    ).total_seconds() < 1
