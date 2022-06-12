from datetime import datetime
import numpy as np
import json
import re


def ymd_to_date(ymd_str):
    ymd_date = None
    valid_formats = ["%Y-%m-%d", "%Y/%m/%d"]
    for vf in valid_formats:
        try:
            ymd_date = datetime.strptime(ymd_str, vf).date()
            break
        except:
            donothing = True
    assert ymd_date != None
    return ymd_date


# Given a dob str in the form YYYY-MM-DD, return the current age in years (including decimal places)
def AgeFromDOB(dob_str):
    assert type(dob_str) == str

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
        age_years = (cur_year - dob_year) + (
            cur_date - bday_thisyear
        ).total_seconds() / (bday_nextyear - bday_thisyear).total_seconds()
    else:
        age_years = (last_year - dob_year) + (
            cur_date - bday_lastyear
        ).total_seconds() / (bday_thisyear - bday_lastyear).total_seconds()

    return age_years


# Given a roman name, make a capitalized version
# e.g., YONG HYEIN -> Yong Hyein
def recapitalize(s):
    return " ".join([x.capitalize() for x in s.split(" ")])


# Given a dictionary of values produce a dictionary of ranks based on those values
# e.g.: {"a": 1, "b": 3.3, "c": 0.5, "d": 1} ->
#       {"a": 2, "b": 4, "c": 1, "d": 2}
def val_dict_to_rank_dict(d, reverse=False):
    table = sorted(
        [(val, key) for key, val in d.items() if (val != None) and not np.isnan(val)],
        reverse=reverse,
    )
    rank_dict = {}
    for j in range(0, len(table)):
        this_item = table[j]
        if j == 0:
            rank_dict[this_item[1]] = j + 1
        else:
            prev_item = table[j - 1]
            if prev_item[0] == this_item[0]:
                rank_dict[this_item[1]] = rank_dict[prev_item[1]]
            else:
                rank_dict[this_item[1]] = j + 1

    for key in d:
        if d[key] == None:
            rank_dict[key] = None
        elif np.isnan(d[key]):
            rank_dict[key] = np.nan

    return rank_dict


# Save df to json table for datatables consumption
def df_to_json_table(df, filepath=None):
    this_json = df.to_json(force_ascii=False, orient="split", index=False)
    # rename "columns" to "header" and arrange on separate lines
    this_json_data = json.loads(this_json)
    this_json_data["header"] = this_json_data.pop("columns")
    this_json_data["data"] = this_json_data.pop("data")
    # note: the above pop-push keeps header ahead of data,
    # since Python 3.7 guarantees insertion order
    if filepath == None:
        return json.dumps(this_json_data, indent=0, ensure_ascii=False)
    else:
        with open(filepath, "w") as f:
            json.dump(this_json_data, f, indent=0, ensure_ascii=False)

# dump json and replace each NaN with null
# This simply does a string replacement. However, there is no reason
# we should ever encounter "NaN" (with that capitalization) in general,
# so it's probably okay.
def dump_json_nan_null(data, filepath, indent=0, ensure_ascii=False):
    s = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    s = re.sub(r"\bNaN\b", "null", s)
    with open(filepath, "w") as f:
        f.write(s)
