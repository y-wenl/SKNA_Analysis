import JSON
using DelimitedFiles
using Statistics
include("shortcuts.jl")

# Useful functions that should be put somewhere else later
function MeanNoMissing(vec)
    vec_nomissing = collect(skipmissing(vec))
    if length(vec_nomissing) == 0
        return missing
    else
        return mean(vec_nomissing)
    end
end
function MeanMissingZero(vec_)
    return mean( @_ vec_ |> replace(__, missing => 0) )
end

# MeanFixMissing = MeanMissingZero
MeanFixMissing = MeanNoMissing

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
member_ids_list = collect(keys(member_info_dict))

# import member vote data (and fix "missing" -> missing)
member_vote_data_in = @_ readdlm(processed_member_data_filepath, ',') |> replace(__, "missing" => missing)
member_vote_arr = member_vote_data_in[2:end,:]
member_vote_header = string <-- Int <-- member_vote_data_in[1,:]
member_n = length(member_vote_header)
member_vote_dict = Dict(member_vote_header[i] => member_vote_arr[:,i] for i in 1:member_n)

# import member vote data (and fix "missing" -> missing)
committee_data_in = @_ readdlm(processed_committee_data_filepath, ',') |> replace(__, "missing" => missing)
committee_arr = committee_data_in[2:end,:]
committee_header = committee_data_in[1,:]
committee_n = length(committee_header)
committee_dict = Dict(committee_header[i] => committee_arr[:,i] for i in 1:committee_n)

bill_n = size(member_vote_arr,1)
@assert bill_n == size(committee_arr,1)

println("done.")



# List parties
parties = @_ map(_["party"], values(member_info_dict)) |> Set |> collect
MembersOfParty = party_ -> (@_ __["member_id"]) <-- @_ filter(_["party"] == party_, collect <| values <| member_info_dict)
members_by_party = Dict(party_ => MembersOfParty(party_) for party_ in parties)

MeanVotesOfMembers = members_ -> collect(MeanFixMissing((@_ __[i]) <-- (@_ member_vote_dict[_] <-- members_)) for i in 1:bill_n)

party_mean_votes_dict = Dict(party_ => MeanVotesOfMembers(MembersOfParty(party_)) for party_ in parties)




# difference of each member to their party
# TODO: come up with a score that weights by how many votes are shared (so that people with only a few votes don't unreasonably high scores)
#   Could potentially be Bayesian?
MemberPartyDifference = (member_, party_) -> (member_vote_dict[member_] - party_mean_votes_dict[party_]).^2 |> MeanFixMissing |> sqrt
diffs_by_member = Dict(member_ =>
                      (
                       Dict(party_ => MemberPartyDifference(member_, party_) for party_ in parties)
                      )
                      for member_ in member_ids_list)
