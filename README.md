# South Korean National Assembly legislative data processing for politopic.net

## Overview
This code processes data scraped from the [National Assembly website](https://likms.assembly.go.kr/bill/main.do) with [y-wenl/SKNADataScraper](https://github.com/y-wenl/SKNADataScraper); the result is used to power [politopic.net](https://politopic.net).

The code has recently been rewritten in Python; the original Julia code remains in the repository for now.

1. `process_data.py` produces the following output:
    1. A list of all bills voted on in the specified session (currently session 21, for 2020-2024).
        - `processed/bill_data_session21.json`, which contains a list of every bill, including the bill name, ID numbers, vote result, and other data.
    2. Each assembly member's vote on each bill
        - `processed/member_vote_data_session21.csv`. Columns list members (by ID) and rows bills. 1 = vote in favor, -1 = vote against, 0 = abstention, empty = no vote.
    3. The committee of each bill
        - `processed/committee_bill_data_session21.csv`. Columns list committees and rows bills. 1 = bill is in the committee, 0 = bill not in the committee.
2. `perform_analyses.py` produces the following output:
    1. A list of data on each member, consisting of unprocessed data like name, district, and ID, as well as new data such as attendance rate and party loyalty. 
        - `processed/members_fullinfo_session21.json`
        - `webdata/members_fullinfo_session21.csv`
    2. A similar list of data on each member, organized in the data format expected by [DataTables](https://datatables.net) for display on [politopic.net](https://politopic.net).
        - `webdata/members_data_session21.json`
    3. For each member, a JSON file listing that member's vote on each bill, as well as their party's vote and the overall bill result. The data format is that expected by [DataTables](https://datatables.net) for display on [politopic.net](https://politopic.net).
        - `webdata/members/`

## Usage

1. Install python 3 and the packages in `requirements.txt` (pyaml, numpy, pandas).

2. Create the data directory `../data` and add the data files `manual_member_info.yaml` and `member_replacements.yaml` from the data repository [y-wenl/SKNAData](https://github.com/y-wenl/SKNAData). These files contain data collected by hand and not scraped.

3. Either run [y-wenl/SKNADataScraper](https://github.com/y-wenl/SKNADataScraper) or add all the data from the data repository [y-wenl/SKNAData](https://github.com/y-wenl/SKNAData) to `../data`.

4. Run `process_data.py`.

5. Run `perform_analyses.py`.

- Output data will be saved to `../data` (there is currently no configuration option, but you can change the `data_super_dir` variable near the top of `process_data.py` and `perform_analyses.py`.

- If you just want the output data, it is available at [y-wenl/SKNAData](https://github.com/y-wenl/SKNAData), which is updated daily.
