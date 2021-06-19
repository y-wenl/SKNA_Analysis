import JSON
using DelimitedFiles

# Data import and setup

session = 21

scrape_data_dir = "../SKNABillVoteData/data/"
bill_subdir = "bills"
member_info_filename = "member_info_data_session$(session).json"

processed_data_dir = "data/"
processed_member_data_filename = "member_vote_data_session$(session).csv"
processed_committee_data_filename = "committee_bill_data_session$(session).csv"


# build filepaths
member_info_filepath = joinpath(scrape_data_dir, member_info_filename)
bill_dir = joinpath(scrape_data_dir, bill_subdir)
processed_member_data_filepath = joinpath(processed_data_dir, processed_member_data_filename)
processed_committee_data_filepath = joinpath(processed_data_dir, processed_committee_data_filename)


# import member info data
print("Reading data...")
@assert(isfile(member_info_filepath))
member_info_json = open(member_info_filepath) do f
    read(f, String)
end
member_info_dict = JSON.parse(member_info_json)

# import member vote data
member_vote_data_in = readdlm(processed_member_data_filepath, ',')
member_vote_arr = member_vote_data_in[2:end,:]
member_vote_header = map(string ∘ Int, member_vote_data_in[1,:])
member_n = length(member_vote_header)
member_vote_dict = Dict(member_vote_header[i] => member_vote_arr[:,i] for i in 1:member_n)

# import member vote data
committee_data_in = readdlm(processed_committee_data_filepath, ',')
committee_arr = committee_data_in[2:end,:]
committee_header = committee_data_in[1,:]
committee_n = length(committee_header)
committee_dict = Dict(committee_header[i] => committee_arr[:,i] for i in 1:committee_n)

println("done.")



# List parties
parties = map(x -> x["party"], values(member_info_dict)) |> Set




# Compute mean vote for each party on a subset of bill data
# function PartyMean(party_name, member_vote_data_subset)
    # filter(x -> , member_vote_data_subset)
# end
