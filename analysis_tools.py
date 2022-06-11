from datetime import datetime

def ymd_to_date(ymd_str):
    ymd_date = None
    valid_formats = ["%Y-%m-%d", "%Y/%m/%d"]
    for vf in valid_formats:
        try:
            ymd_date = datetime.strptime(ymd_str, vf).date()
            break
        except:
            donothing = True
    assert(ymd_date != None)
    return ymd_date

# Given a dob str in the form YYYY-MM-DD, return the current age in years (including decimal places)
def AgeFromDOB(dob_str):
    assert(type(dob_str) == str)

    dob_date = ymd_to_date(dob_str)

    # compute years based on birthday, and extra time since then
    # NOTE: we don't really need this to be perfect, so we're not worrying about timezones and stuff

    cur_date = datetime.now().date()

    dob_year = dob_date.year
    dob_month = dob_date.month
    dob_day = dob_date.day

    cur_year = cur_date.year
    last_year = cur_year - 1
    next_year = cur_year + 1


    bday_thisyear = datetime(cur_year, dob_month, dob_day).date()
    bday_lastyear = datetime(last_year, dob_month, dob_day).date()
    bday_nextyear = datetime(next_year, dob_month, dob_day).date()

    if cur_date >= bday_thisyear:
        age_years = (cur_year - dob_year) + (cur_date - bday_thisyear).total_seconds()/(bday_nextyear - bday_thisyear).total_seconds()
    else:
        age_years = (last_year - dob_year) + (cur_date - bday_lastyear).total_seconds()/(bday_thisyear - bday_lastyear).total_seconds()

    return age_years


# Given a roman name, make a capitalized version
# e.g., YONG HYEIN -> Yong Hyein
def recapitalize(s):
    return " ".join([x.capitalize() for x in s.split(" ")])
