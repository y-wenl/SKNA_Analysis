import os
import glob
from copy import copy

import json

import numpy as np
import pandas as pd

# turn on or off debugging
debug = False

# set session
session = 21

# set main data directory
data_super_dir = "../data/"

# set up subdirectories and filepaths
scrape_data_dir = data_super_dir
bill_subdir = "bills"
member_info_filename = f"member_info_data_session{session}.json"

processed_data_dir = os.path.join(data_super_dir, "processed/")
# processed_data_dir = "ignore/"
processed_bill_data_filename = f"bill_data_session{session}.json"
processed_vote_data_filename = f"member_vote_data_session{session}.csv"
processed_committee_data_filename = f"committee_bill_data_session{session}.csv"

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

print("Reading member data")

# import member list
assert os.path.isfile(member_info_filepath)
with open(member_info_filepath, "r") as f:
    member_info = json.load(f)
member_ids = sorted(member_info.keys())

print("Reading bill data")
# import bill data
bill_filepaths = glob.glob(os.path.join(bill_dir, f"bill_data_session{session}_*json"))
bill_filepaths = sorted(bill_filepaths)
assert len(bill_filepaths) > 0

if debug:
    print("WARNING: DEBUG ENGAGED")
    bill_filepaths = bill_filepaths[0:10]  # DEBUG only do 10 bills


# read in bill data
# we construct 2 versions: 1 full set of data and one "lite" version with vote data removed (for saving to a json file)
bill_dicts = []
bill_dicts_lite = []
lite_keys_to_delete = ["members_agree", "members_oppose", "members_abstain", "summary"]
for bill_filepath in bill_filepaths:
    with open(bill_filepath, "r") as f:
        this_bill_data = json.load(f)
        bill_dicts.append(this_bill_data)
        this_bill_data_lite = copy(this_bill_data)
        for key in lite_keys_to_delete:
            this_bill_data_lite.pop(key, None)
        bill_dicts_lite.append(this_bill_data_lite)


##### MEMBER VOTE LISTS #####
print("Constructing member votes data")
# for each member, construct a vector of votes: 1 for yes, -1 for no, 0 for abstain, None for not present
def memberid_to_votevector(member_id):
    agree_val = 1
    oppose_val = -1
    abstain_val = 0

    # Note: np doesn't support nan with ints, so we use pd.Int8Dtype
    agree_vector = pd.array(
        [
            1
            if member_id in [_["member_id"] for _ in bill_data["members_agree"]]
            else 0
            for bill_data in bill_dicts
        ]
    ).astype(pd.Int8Dtype())
    oppose_vector = pd.array(
        [
            1
            if member_id in [_["member_id"] for _ in bill_data["members_oppose"]]
            else 0
            for bill_data in bill_dicts
        ]
    ).astype(pd.Int8Dtype())
    abstain_vector = pd.array(
        [
            1
            if member_id in [_["member_id"] for _ in bill_data["members_abstain"]]
            else 0
            for bill_data in bill_dicts
        ]
    ).astype(pd.Int8Dtype())

    # skip vector puts nan on every vote for which the member is registered as none of agree, oppose, or abstain
    skip_vector_nan = pd.array(
        [
            np.nan if (x == 0) else 0
            for x in (agree_vector + oppose_vector + abstain_vector)
        ]
    ).astype(pd.Int8Dtype())

    assert len(agree_vector) == len(bill_dicts)
    assert len(oppose_vector) == len(bill_dicts)
    assert len(abstain_vector) == len(bill_dicts)
    assert np.dot(agree_vector, oppose_vector) == 0
    assert np.dot(oppose_vector, abstain_vector) == 0
    assert np.dot(abstain_vector, agree_vector) == 0

    output_vector = (
        agree_val * agree_vector
        + oppose_val * oppose_vector
        + abstain_val * abstain_vector
        + skip_vector_nan
    )
    assert len(output_vector) == len(bill_dicts)
    return output_vector


member_votes_dict = {
    member_id: memberid_to_votevector(member_id) for member_id in member_ids
}


##### COMMITTEES #####
print("Constructing committee data")
# Construct lists for committees
committees = sorted(list(set([x["committee"] for x in bill_dicts])))
committees_bill_dict = {
    committee: np.array([bd["committee"] == committee for bd in bill_dicts]).astype(int)
    for committee in committees
}
# committee_data_array = np.array([[bd["committee"] == committee for committee in committees] for bd in bill_dicts]).astype(int)


##### SAVE DATA #####
print("Setting up output")

# Save results to csv files
# Note: Unlike Julia version, we now save bill id too (to be safe)

# create processed data dir if it doesn't exist
if not os.path.isdir(processed_data_dir):
    os.mkdir(processed_data_dir)

# create member data with header
member_votes_df = pd.DataFrame(member_votes_dict, columns=member_ids)
member_votes_df.insert(
    0, "bill_id", [x["bill_id"] for x in bill_dicts_lite], allow_duplicates=False
)

# create committee data with header
committees_bill_df = pd.DataFrame(committees_bill_dict, columns=committees)
committees_bill_df.insert(
    0, "bill_id", [x["bill_id"] for x in bill_dicts_lite], allow_duplicates=False
)

if not debug:
    print("Writing data")
    member_votes_df.to_csv(processed_vote_data_filepath, index=False)
    committees_bill_df.to_csv(processed_committee_data_filepath, index=False)

    with open(processed_bill_data_filepath, "w") as f:
        json.dump(bill_dicts_lite, f, indent=4, ensure_ascii=False)
