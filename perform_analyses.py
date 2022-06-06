import os
from copy import copy

import json
import yaml

import numpy as np
import pandas as pd

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
member_vote_df = pd.read_csv(processed_vote_data_filepath)
bill_ids = list(member_vote_df["bill_id"])

# import committee data
committee_bill_df = pd.read_csv(processed_committee_data_filepath)
bill_ids_committee = list(committee_bill_df["bill_id"])
# ensure that bill data is in the correct order
assert all([x == y for x, y in zip(bill_ids, bill_ids_committee)])

# import bill data
print("Reading bill data")
assert os.path.isfile(processed_bill_data_filepath)
with open(processed_bill_data_filepath, "r") as f:
    bill_data = json.load(f)


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
