from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import List, Optional

import requests

from src.constants import API_VERSION, BACKEND_URL, DOCKER, LOCAL_PUBLISHER, PROD
from src.data.github.graphql import GraphQLErrorRateLimit
from src.data.mongo.secret import update_keys
from src.data.mongo.user_months import UserMonth, get_user_months, set_user_month
from src.models.user.main import UserPackage
from src.subscriber.aggregation import get_user_data
from src.utils import alru_cache, date_to_datetime

s = requests.Session()

# NOTE: query user from PubSub, not from subscriber user router


async def query_user_month(
    user_id: str,
    access_token: Optional[str],
    private_access: bool,
    start_date: date,
    retries: int = 0,
) -> Optional[UserMonth]:
    year, month = start_date.year, start_date.month
    end_day = monthrange(year, month)[1]
    end_date = date(year, month, end_day)

    try:
        data = await get_user_data(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            timezone_str="US/Eastern",
            access_token=access_token,
            catch_errors=retries > 0,
        )
    except GraphQLErrorRateLimit:
        return None
    except Exception:
        # Retry, catching exceptions and marking incomplete this time
        if retries < 1:
            await query_user_month(
                user_id, access_token, private_access, start_date, retries + 1
            )
        return None

    month_completed = datetime.now() > date_to_datetime(end_date) + timedelta(days=1)
    user_month = UserMonth.parse_obj(
        {
            "user_id": user_id,
            "month": date_to_datetime(start_date),
            "version": API_VERSION,
            "private": private_access,
            "complete": retries == 0 and month_completed,
            "data": data,
        }
    )

    await set_user_month(user_month)
    return user_month


# NOTE: can only be called once every 1-2 minutes from publisher due to separate alru_cache
@alru_cache(ttl=timedelta(hours=6))
async def query_user(
    user_id: str,
    access_token: Optional[str],
    private_access: bool = False,
    start_date: date = date.today() - timedelta(365),
    end_date: date = date.today(),
) -> Optional[UserPackage]:
    await update_keys()

    curr_data: List[UserMonth] = await get_user_months(
        user_id, private_access, start_date, end_date
    )
    curr_months = [x.month for x in curr_data if x.complete]

    month, year = start_date.month, start_date.year
    months: List[date] = []
    while date(year, month, 1) <= end_date:
        start = date(year, month, 1)
        if date_to_datetime(start) not in curr_months:
            months.append(start)
        month = month % 12 + 1
        year = year + (month == 1)

    all_user_packages: List[UserPackage] = [x.data for x in curr_data]
    for month in months:
        temp = await query_user_month(user_id, access_token, private_access, month)
        if temp is not None:
            all_user_packages.append(temp.data)

    out: Optional[UserPackage] = None
    if len(all_user_packages) > 0:
        out = all_user_packages[0]
        for user_package in all_user_packages[1:]:
            out += user_package

    if len(months) > 1:
        # cache buster for publisher
        if PROD:
            s.get(BACKEND_URL + "/user/" + user_id + "?no_cache=True")
        elif DOCKER:
            s.get(LOCAL_PUBLISHER + "/user/" + user_id + "?no_cache=True")

        return (False, out)  # type: ignore

    # only cache if just the current month updated
    return (True, out)  # type: ignore
