import os
from copy import copy

import json
import yaml

import numpy as np
import pandas as pd

from datetime import datetime

from analysis_tools import *


##### Data import and setup #####

# set session
session = 21

# set main data directory
data_super_dir = "../data/"

# output filenames
output_data_dir = os.path.join(data_super_dir, "webdata/")
# output_data_dir = "ignore/"
output_member_data_dir = os.path.join(output_data_dir, "members/")
members_fullinfo_filename = f"members_fullinfo_session{session}.json"
members_fullinfo_csv_filename = f"members_fullinfo_session{session}.csv"
member_vote_filename_base = f"member_vote_data_{session}_ID.json"

# set up subdirectories and filepaths
scrape_data_dir = data_super_dir
bill_subdir = "bills"
member_info_filename = f"member_info_data_session{session}.json"
member_reps_filename = "member_replacements.yaml"
member_manual_filename = "manual_member_info.yaml"

processed_data_dir = os.path.join(data_super_dir, "processed/")
# processed_data_dir = "ignore/"
processed_bill_data_filename = f"bill_data_session{session}.json"
processed_vote_data_filename = f"member_vote_data_session{session}.csv"
processed_committee_data_filename = f"committee_bill_data_session{session}.csv"

member_reps_filepath = os.path.join(data_super_dir, member_reps_filename)
member_manual_filepath = os.path.join(data_super_dir, member_manual_filename)
member_info_filepath = os.path.join(scrape_data_dir, member_info_filename)
bill_dir = os.path.join(scrape_data_dir, bill_subdir)
processed_bill_data_filepath = os.path.join(
    processed_data_dir, processed_bill_data_filename
)
processed_vote_data_filepath = os.path.join(
    processed_data_dir, processed_vote_data_filename
)
processed_committee_data_filepath = os.path.join(
    processed_data_dir, processed_committee_data_filename
)

# output filepaths
members_fullinfo_filepath = os.path.join(output_data_dir, members_fullinfo_filename)
members_fullinfo_csv_filepath = os.path.join(
    output_data_dir, members_fullinfo_csv_filename
)

# create output directories if necessary
if not os.path.isdir(output_data_dir):
    os.mkdir(output_data_dir)
if not os.path.isdir(output_member_data_dir):
    os.mkdir(output_member_data_dir)


# import member list
print("Reading member data")
assert os.path.isfile(member_info_filepath)
with open(member_info_filepath, "r") as f:
    member_info_data = json.load(f)
member_ids = sorted(member_info_data.keys())

# import member vote data
member_vote_df_full = pd.read_csv(processed_vote_data_filepath)
member_n = len(member_vote_df_full.columns) - 1
bill_ids_member = list(member_vote_df_full["bill_id"])
member_ids_in_df = sorted(
    [x for x in list(member_vote_df_full.columns) if x != "bill_id"]
)
assert set(member_ids) == set(member_ids_in_df)
member_vote_df = member_vote_df_full[member_ids]  # remove bill_id column

# import committee data
committee_bill_df_full = pd.read_csv(processed_committee_data_filepath)
committee_n = len(committee_bill_df_full.columns) - 1
bill_ids_committee = list(committee_bill_df_full["bill_id"])
committees = sorted([x for x in list(committee_bill_df_full.columns) if x != "bill_id"])
committee_bill_df = committee_bill_df_full[committees]  # remove bill_id column

# import bill data
print("Reading bill data")
assert os.path.isfile(processed_bill_data_filepath)
with open(processed_bill_data_filepath, "r") as f:
    bill_data = json.load(f)
bill_ids = [x["bill_id"] for x in bill_data]
bill_n = len(bill_ids)

# ensure that bill data is in the correct order
assert all([x == y for x, y in zip(bill_ids, bill_ids_member)])
assert all([x == y for x, y in zip(bill_ids, bill_ids_committee)])


# import manual member info and update member_info_data accordingly
assert os.path.isfile(member_manual_filepath)
with open(member_manual_filepath, "r") as f:
    input_member_manual_datas = yaml.safe_load(f)
for mmd in input_member_manual_datas:
    if str(mmd["session"]) == str(session):
        for this_mm in mmd["data"]:
            this_id = str(this_mm["member_id"])
            this_name = this_mm["name"]

            assert this_id in member_info_data
            assert member_info_data[this_id]["name"] == this_name

            # update member_info_data
            member_info_data[this_id].update(this_mm)
        break  # exit when we've done our session


# import member replacement data and validate it
assert os.path.isfile(member_reps_filepath)
with open(member_reps_filepath, "r") as f:
    input_member_reps_datas = yaml.safe_load(f)

member_reps_dict = {}
for mrd in input_member_reps_datas:
    if str(mrd["session"]) == str(session):
        for this_mr in mrd["data"]:
            this_id = str(this_mr["member_id"])
            this_name = this_mr["name"]

            assert this_id in member_info_data
            assert member_info_data[this_id]["name"] == this_name
            member_reps_dict[this_id] = this_mr

            # update member_info_data
            member_info_data[this_id].update(this_mr)
        break  # exit when we've done our session

# Create data on member voting: nan for not in chamber (left or not yet joined); 1 for voted; 0 for absent
member_didvote_df = member_vote_df.applymap(lambda x: int(not np.isnan(x)))
bill_dates = [ymd_to_date(x["vote_date"]) for x in bill_data]
bill_dates_df = pd.DataFrame({"bill_date": bill_dates})

for mid in member_reps_dict:
    this_mr = member_reps_dict[mid]
    this_voted_dates = [
        b for b, _ in zip(bill_dates, list(member_didvote_df[mid])) if _ == 1
    ]

    if "date_left" in this_mr:
        left_date = ymd_to_date(this_mr["date_left"])
        if this_voted_dates:
            last_vote_date = max(this_voted_dates)
            if left_date != last_vote_date:
                if left_date < last_vote_date:
                    print(
                        f"WARNING! YAML states {member_info_data[mid]['name']} ({mid}) left office on {left_date} but last vote was {last_vote_date}."
                    )
                else:
                    print(
                        f"YAML states {member_info_data[mid]['name']} ({mid}) left office on {left_date}; last vote was {last_vote_date}. (OK)"
                    )

        member_didvote_df.loc[bill_dates_df["bill_date"] > left_date, mid] = np.nan

    if "date_joined" in this_mr:
        joined_date = ymd_to_date(this_mr["date_joined"])
        if this_voted_dates:
            first_vote_date = min(this_voted_dates)
            if joined_date != first_vote_date:
                if joined_date > first_vote_date:
                    print(
                        f"WARNING! YAML states {member_info_data[mid]['name']} ({mid}) joined office on {joined_date} but first vote was {first_vote_date}."
                    )
                else:
                    print(
                        f"YAML states {member_info_data[mid]['name']} ({mid}) joined office on {joined_date}; first vote was {first_vote_date}. (OK)"
                    )

        member_didvote_df.loc[bill_dates_df["bill_date"] < joined_date, mid] = np.nan


member_votenan_df = member_vote_df.applymap(lambda x: 1 if not np.isnan(x) else np.nan)

##### TRANSLATE COMMITTEES AND BILL DATA #####

committee_english_table = {
    "과학기술정보방송통신위원회": "Science, ICT, Future Planning, Broadcasting and Communications Committee",
    "교육위원회": "Education Committee",
    "국방위원회": "National Defense Committee",
    "국토교통위원회": "Land, Infrastructure and Transport Committee",
    "국회운영위원회": "House Steering Committee",
    "기획재정위원회": "Strategy and Finance Committee",
    "농림축산식품해양수산위원회": "Agriculture, Food, Rural Affairs, Oceans and Fisheries Committee",
    "문화체육관광위원회": "Culture, Sports and Tourism Committee",
    "법제사법위원회": "Legislation and Judiciary Committee",
    "보건복지위원회": "Health and Welfare Committee",
    "산업통상자원중소벤처기업위원회": "Trade, Industry, Energy, SMEs, and Startups Committee",
    "여성가족위원회": "Gender Equality and Family Committee",
    "외교통일위원회": "Foreign Affairs and Unification Committee",
    "정무위원회": "National Policy Committee",
    "정보위원회": "Intelligence Committee",
    "행정안전위원회": "Public Administration and Security Committee",
    "환경노동위원회": "Environment and Labor Committee",
    "정치개혁 특별위원회": "Special Committee on Political Reform",
    "국회상임위원회 위원 정수에 관한 규칙 개정 특별위원회": "Special Committee on Standing Committee Member Number Rules",
    "본회의": "Plenary",
    "예산결산특별위원회": "Special Committee on Budget and Accounts",
    "윤리특별위원회": "Special Committee on Ethics",
}

result_english_table = {
    "부결": "Rejected",
    "원안가결": "Passed",
    "수정가결": "Passed (revised)",
}
kind_english_table = {
    "동의안": "Agreement",
    "결의안": "Resolution",
    "예산안": "Budget bill",
    "결산": "Settlement of accounts",
    "승인안": "Approval",
    "중요동의": "Main motion",
    "규칙안": "Draft regulation",
    "법률안": "Legislative bill",
}

for mid in member_info_data:
    member_info_data[mid]["committees"] = [
        c for c in member_info_data[mid]["committees"] if c
    ]
    this_committees = member_info_data[mid]["committees"]
    member_info_data[mid]["committees_en"] = [
        committee_english_table.get(c, c) for c in this_committees
    ]

for bd in bill_data:
    this_committee = bd["committee"]
    bd["committee_en"] = committee_english_table.get(this_committee, this_committee)

    bd["result_en"] = result_english_table[bd["result"]]
    bd["kind_en"] = kind_english_table.get(bd["kind"], bd["kind"])


##### FIX PARTIES #####

# set party equivalences
# notes:
# 1) 미래통합당 is the platform party of 국민의힘
# 2) 더불어시민당 is the platform party of 더불어민주당
# 3) 열린민주당 merged into 더불어민주당 in early 2022
party_equivalence_table = {
    "더불어민주당": "더불어민주당",
    "더불어시민당": "더불어민주당",
    "열린민주당": "더불어민주당",
    "국민의힘": "국민의힘",
    "미래통합당": "국민의힘",
    "정의당": "정의당",
    "국민의당": "국민의당",
    "기본소득당": "기본소득당",
    "시대전환": "시대전환",
    "무소속": "무소속",
}
for mid in member_info_data:
    member_info_data[mid]["party_group"] = party_equivalence_table[
        member_info_data[mid]["party"]
    ]

major_parties = ["더불어민주당", "국민의힘", "정의당"]

party_english_table = {
    "더불어민주당": "Democratic Party of Korea",
    "더불어시민당": "Platform Party",
    "열린민주당": "Open Democratic Party",
    "국민의힘": "People Power Party",
    "미래통합당": "United Future Party",
    "정의당": "Justice Party",
    "국민의당": "People Party",
    "기본소득당": "Basic Income Party",
    "시대전환": "Transition Korea",
    "무소속": "Unaffiliated",
}
for mid in member_info_data:
    member_info_data[mid]["party_en"] = party_english_table[
        member_info_data[mid]["party"]
    ]
    member_info_data[mid]["party_group_en"] = party_english_table[
        member_info_data[mid]["party_group"]
    ]

##### Compute means and party differences #####
print("Computing means and party differences")

# List parties
parties = sorted(list(set([member_info_data[x]["party_group"] for x in member_ids])))
members_by_party = {
    party: [x for x in member_ids if member_info_data[x]["party_group"] == party]
    for party in parties
}
assert len(set(parties).intersection(set(major_parties))) == len(major_parties)

# Compute party data for each bill
# 1) mean
# 2) sign of mean (is most of party for or against)
# 3) number and percent of party members voting (in any direction)
# Note: we ignore missing votes, but abstentions are 0
party_mean_df = pd.DataFrame(
    {party: member_vote_df[members_by_party[party]].mean(axis=1) for party in parties},
    columns=parties,
)
party_sign_df = party_mean_df.applymap(np.sign)

party_numvoted_df = pd.DataFrame(
    {
        party: member_didvote_df[members_by_party[party]].sum(axis=1)
        for party in parties
    },
    columns=parties,
)
party_percvoted_df = pd.DataFrame(
    {
        party: member_didvote_df[members_by_party[party]].sum(axis=1)
        / len(members_by_party[party])
        for party in parties
    },
    columns=parties,
)


# difference of each member to their party
# TODO: come up with a score that weights by how many votes are shared (so that people with only a few votes don't unreasonably high scores)
#   Could potentially be Bayesian?

# Idea: let v_p represent the mean party vote vector and v_i be some individual vote vector
# We will define party loyalty as v_p . v_i, normalized
# Let n_p and n_i be the number of non-nan votes. Note that n_p >= n_i.
# Then, (1/n_i) v_p . v_i is the numerator, and must be between -1 and 1.
# We normalize this by sqrt[ (1/n_p) v_p . v_p ], i.e., the root mean party vote.

# old method loyalty score: 1 - 0.5 sqrt[ (vi - vp)^2/n_i  ]

normalized_dot = lambda u, v: np.nansum(u * v) / ((u * v).count())
normalized_dotself = lambda u: normalized_dot(u, u)

loyalty_score_dot = {}
loyalty_score_rms = {}
loyalty_score_abs = {}
for party in parties:
    for mid in members_by_party[party]:
        if party == "무소속":
            loyalty_score_dot[mid] = np.nan
            loyalty_score_rms[mid] = np.nan
            loyalty_score_abs[mid] = np.nan
        else:
            vivp = normalized_dot(member_vote_df[mid], party_mean_df[party])
            vpvp = np.sqrt(
                normalized_dot(
                    member_votenan_df[mid] * party_mean_df[party],
                    member_votenan_df[mid] * party_mean_df[party],
                )
            )
            vivi = np.sqrt(normalized_dot(member_vote_df[mid], member_vote_df[mid]))
            loyalty_score_dot[mid] = vivp / (vpvp * vivi)

            loyalty_score_rms[mid] = 1 - 0.5 * np.sqrt(
                normalized_dotself(member_vote_df[mid] - party_mean_df[party])
            )

            loyalty_score_abs[mid] = normalized_dotself(
                member_vote_df[mid] * party_sign_df[party]
            )

##### Frequency voting with DP majority #####

# # let's compute the vote table for DP only for each bill
# dpvotes=member_vote_df[members_by_party["더불어민주당"]].apply(pd.Series.value_counts, axis=1)

member_party_votefreq_dfs = {}
member_party_votefreqs = {}
for party in major_parties:
    this_vf_df = pd.DataFrame(
        {
            mid: ((member_vote_df[mid] == party_sign_df[party]).astype(int))
            * member_votenan_df[mid]
            for mid in member_ids
        },
        columns=member_ids,
    )
    member_party_votefreq_dfs[party] = this_vf_df
    member_party_votefreqs[party] = dict((this_vf_df.sum() / this_vf_df.count()))

member_party_alignments = {}
for party in ["더불어민주당", "국민의힘", "정의당"]:
    member_party_alignments[party] = {}
    for mid in member_ids:
        vivp = normalized_dot(member_vote_df[mid], party_mean_df[party])
        vpvp = np.sqrt(
            normalized_dot(
                member_votenan_df[mid] * party_mean_df[party],
                member_votenan_df[mid] * party_mean_df[party],
            )
        )
        vivi = np.sqrt(normalized_dot(member_vote_df[mid], member_vote_df[mid]))
        member_party_alignments[party][mid] = vivp / (vpvp * vivi)


##### Attendance rates #####
print("Computing attendance rates")
member_absenteeism = {
mid: 1 - (member_didvote_df[mid].sum() / member_didvote_df[mid].count())
for mid in member_ids
}
member_attendance = {
    mid: (member_didvote_df[mid].sum() / member_didvote_df[mid].count())
    for mid in member_ids
}

##### Ages #####
print("Computing ages")
member_ages = {mid: AgeFromDOB(member_info_data[mid]["dob"]) for mid in member_ids}

##### Party average data #####
party_median_ages = {
    party: np.median([member_ages[mid] for mid in members_by_party[party]])
    for party in parties
}
party_median_attendance = {
    party: np.median([member_attendance[mid] for mid in members_by_party[party]])
    for party in parties
}
party_median_loyalty = {
    party: np.median([loyalty_score_dot[mid] for mid in members_by_party[party]])
    for party in parties
}
party_size = {party: len(members_by_party[party]) for party in parties}
party_women = {
    party: len(
        [
            mid
            for mid in members_by_party[party]
            if member_info_data[mid]["gender"] == "F"
        ]
    )
    for party in parties
}
party_women_frac = {party: party_women[party] / party_size[party] for party in parties}

##### Update member_info_data #####

# compute ranks for loyalty_score_dot and attendance
loyalty_score_dot_rank = val_dict_to_rank_dict(loyalty_score_dot, reverse=True)
attendance_rank = val_dict_to_rank_dict(member_attendance, reverse=True)
absenteeism_rank = val_dict_to_rank_dict(member_absenteeism, reverse=True)
loyalty_score_dot_party_rank = {}
attendance_party_rank = {}
absenteeism_party_rank = {}
for party in parties:
    if party == "무소속":
        loyalty_score_dot_party_rank.update(
            {
                k: np.nan
                for k, v in loyalty_score_dot.items()
                if k in members_by_party[party]
            }
        )
        attendance_party_rank.update(
            {
                k: np.nan
                for k, v in member_attendance.items()
                if k in members_by_party[party]
            }
        )
        absenteeism_party_rank.update(
            {
                k: np.nan
                for k, v in member_absenteeism.items()
                if k in members_by_party[party]
            }
        )
    else:
        this_loyalty_score_dot_party = {
            k: v for k, v in loyalty_score_dot.items() if k in members_by_party[party]
        }
        this_attendance_party = {
            k: v for k, v in member_attendance.items() if k in members_by_party[party]
        }
        this_absenteeism_party = {
            k: v for k, v in member_absenteeism.items() if k in members_by_party[party]
        }

        loyalty_score_dot_party_rank.update(
            val_dict_to_rank_dict(this_loyalty_score_dot_party, reverse=True)
        )
        attendance_party_rank.update(
            val_dict_to_rank_dict(this_attendance_party, reverse=True)
        )
        absenteeism_party_rank.update(
            val_dict_to_rank_dict(this_absenteeism_party, reverse=True)
        )

for mid in member_info_data:
    # Fix capitalization of roman names
    member_info_data[mid]["roman_name"] = recapitalize(
        member_info_data[mid]["roman_name"]
    )

    member_info_data[mid]["age"] = member_ages[mid]
    member_info_data[mid]["attendance"] = member_attendance[mid]
    member_info_data[mid]["absenteeism"] = member_absenteeism[mid]

    member_info_data[mid]["dp_vote_freq"] = member_party_votefreqs["더불어민주당"][mid]
    # member_info_data[mid]["gugmin_vote_freq"] = member_party_votefreqs["국민의힘"][mid]
    # member_info_data[mid]["jeong_vote_freq"] = member_party_votefreqs["정의당"][mid]
    member_info_data[mid]["dp_alignment"] = member_party_alignments["더불어민주당"][mid]
    member_info_data[mid]["gugmin_alignment"] = member_party_alignments["국민의힘"][mid]
    member_info_data[mid]["jeong_alignment"] = member_party_alignments["정의당"][mid]
    member_info_data[mid]["loyalty"] = loyalty_score_dot[mid]
    # member_info_data[mid]["loyalty_score_rms"] = loyalty_score_rms[mid]
    # member_info_data[mid]["loyalty_score_abs"] = loyalty_score_abs[mid]

    member_info_data[mid]["loyalty_rank"] = loyalty_score_dot_rank[mid]
    member_info_data[mid]["attendance_rank"] = attendance_rank[mid]
    member_info_data[mid]["absenteeism_rank"] = absenteeism_rank[mid]
    member_info_data[mid]["loyalty_party_rank"] = loyalty_score_dot_party_rank[mid]
    member_info_data[mid]["attendance_party_rank"] = attendance_rank[mid]
    member_info_data[mid]["absenteeism_party_rank"] = absenteeism_rank[mid]

    this_party_group = member_info_data[mid]["party_group"]
    this_party = member_info_data[mid]["party"]
    this_party_fullname = this_party
    if this_party != this_party_group:
        this_party_fullname = f"{this_party} ({this_party_group})"
    member_info_data[mid]["party_fullname"] = this_party_fullname

    this_party_group_en = member_info_data[mid]["party_group_en"]
    this_party_en = member_info_data[mid]["party_en"]
    this_party_en_fullname = this_party_en
    if this_party_en != this_party_group_en:
        this_party_en_fullname = f"{this_party_en} ({this_party_group_en})"
    member_info_data[mid]["party_en_fullname"] = this_party_en_fullname

    member_info_data[mid]["partysize"] = len(members_by_party[this_party_group])
    member_info_data[mid]["totalmembers"] = len(member_ids)

##### Save data into a data structure #####
print("Saving members fullinfo json...")
with open(members_fullinfo_filepath, "w") as f:
    json.dump(member_info_data, f, indent=4, ensure_ascii=False)

print("Saving members fullinfo csv...")
member_output_df = pd.DataFrame.from_dict(
    member_info_data,
    orient="index",
    columns=[
        "name",
        "name_alt",
        "roman_name",
        "gender",
        "dob",
        "age",
        "district",
        "terms",
        "party",
        "party_en",
        "party_group",
        "party_group_en",
        "loyalty",
        "loyalty_rank",
        "attendance",
        "attendance_rank",
        "absenteeism",
        "absenteeism_rank",
        "dp_vote_freq",
        "dp_alignment",
        "jeong_alignment",
        "gugmin_alignment",
    ],
)
member_output_df.index.name = "member_id"
member_output_df.to_csv(members_fullinfo_csv_filepath)

print("Saving individual member data...")
bill_data_df = pd.DataFrame(
    bill_data,
    columns=[
        "vote_date",
        "result",
        "result_en",
        "name",
        "committee",
        "committee_en",
        "bill_id",
        "bill_no",
        "id_master",
        "kind",
        "kind_en",
    ],
)
bill_data_df.rename(columns={"vote_date": "date"}, inplace=True)
for mid in member_ids:
    this_filename = member_vote_filename_base.replace("ID", str(mid))
    this_filepath = os.path.join(output_member_data_dir, this_filename)

    this_party = member_info_data[mid]["party_group"]

    this_bill_df = bill_data_df.copy()

    # add data: member_vote and party_vote
    this_bill_df = this_bill_df.assign(
        member_vote=member_vote_df[mid].astype(pd.Int8Dtype()),
        party_vote=party_sign_df[this_party],
    )

    this_bill_df = this_bill_df[~np.isnan(member_didvote_df[mid])]

    this_bill_json = this_bill_df.to_json(
        force_ascii=False, orient="split", index=False
    )
    # rename "columns" to "header" and arrange on separate lines
    this_bill_json_data = json.loads(this_bill_json)
    this_bill_json_data["header"] = this_bill_json_data.pop("columns")
    this_bill_json_data["data"] = this_bill_json_data.pop("data")
    # note: the above pop-push keeps header ahead of data,
    # since Python 3.7 guarantees insertion order
    with open(this_filepath, "w") as f:
        json.dump(this_bill_json_data, f, indent=0, ensure_ascii=False)


# TODO: save party output

# TODO: save party output
# print("Saving party data...")
party_output_df = pd.DataFrame(
    {
        "party_median_ages": party_median_ages,
        "party_median_attendance": party_median_attendance,
        "party_median_loyalty": party_median_loyalty,
        "party_size": party_size,
        "party_women": party_women,
        "party_women_frac": party_women_frac,
    }
)
party_mean_df
party_numvoted_df
