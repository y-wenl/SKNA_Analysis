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

# set up subdirectories and filepaths
scrape_data_dir = data_super_dir
bill_subdir = "bills"
member_info_filename = f"member_info_data_session{session}.json"
member_reps_filename = "member_replacements.yaml"

# processed_data_dir = os.path.join(data_super_dir, "processed/")
processed_data_dir = "ignore/"
processed_bill_data_filename = f"bill_data_session{session}.json"
processed_vote_data_filename = f"member_vote_data_session{session}.csv"
processed_committee_data_filename = f"committee_bill_data_session{session}.csv"

member_reps_filepath = os.path.join(data_super_dir, member_reps_filename)
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


# import member replacement data and validate it
# TODO: ignore invalid data instead of dying?
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
        break

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


##### Compute means and party differences #####
print("Computing means and party differences")

# List parties
parties = sorted(list(set([member_info_data[x]["party"] for x in member_ids])))
members_by_party = {
    party: [x for x in member_ids if member_info_data[x]["party"] == party]
    for party in parties
}

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

member_dpvote_df = pd.DataFrame(
    {
        mid: ((member_vote_df[mid] == party_sign_df["더불어민주당"]).astype(int))
        * member_votenan_df[mid]
        for mid in member_ids
    },
    columns=member_ids,
)
member_dpvotefreq_dict = dict((member_dpvote_df.sum() / member_dpvote_df.count()))

##### Absentee rates #####
print("Computing absentee rates")
member_absenteeism = {
    mid: member_didvote_df[mid].sum() / member_didvote_df[mid].count()
    for mid in member_ids
}

##### Ages #####
print("Computing ages")
member_ages = {mid: AgeFromDOB(member_info_data[mid]["dob"]) for mid in member_ids}


##### Save data into a data structure #####
# TODO
member_output_df = pd.DataFrame(
    {
        "age": member_ages,
        "absenteeism": member_absenteeism,
        "dp_vote_freq": member_dpvotefreq_dict,
        "loyalty_score_dot": loyalty_score_dot,
        "loyalty_score_rms": loyalty_score_rms,
        "loyalty_score_abs": loyalty_score_abs,
    }
)

party_mean_df
party_numvoted_df
