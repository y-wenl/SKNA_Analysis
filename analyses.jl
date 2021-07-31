import JSON
using DelimitedFiles
using Statistics
using Dates
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
function MeanMissingN1(vec_)
    return mean( @_ vec_ |> replace(__, missing => -1) )
end
function RemoveMissing(vec_)
    return filter(x -> ~ismissing(x), vec_)
end
function AgeFromDOB(dob_str)
    if typeof(dob_str) != String
        return missing
    end
    if match(r"[12][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]", dob_str) |> isnothing
        return missing
    end

    local dob = Date(dob_str)
    local hoy = today()
    local age = Dates.year(hoy) - Dates.year(dob)
    if (Dates.month(hoy) < Dates.month(dob)) ||
        (
        (Dates.month(hoy) == Dates.month(dob)) &&
        (Dates.day(hoy) < Dates.day(dob))
       )
        age = age - 1

        earlier_date = Date(string(Dates.year(hoy) - 1)*"-"*Dates.format(dob, "mm-dd"))
    else
        earlier_date = Date(string(Dates.year(hoy) - 0)*"-"*Dates.format(dob, "mm-dd"))
    end
    # add in days
    age = age + Dates.value(hoy - earlier_date)/365

    return age
end

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
members = collect(keys(member_info_dict))

# import member vote data (and fix "missing" -> missing)
member_vote_data_in = @_ readdlm(processed_member_data_filepath, ',') |> replace(__, "missing" => missing)
member_vote_arr = member_vote_data_in[2:end,:]
member_vote_header = string <-- Int <-- member_vote_data_in[1,:]
member_n = length(member_vote_header)
member_vote_dict = Dict(member_vote_header[i] => member_vote_arr[:,i] for i in 1:member_n)
member_vote_dict_missingzero = Dict(member_vote_header[i] => replace(member_vote_arr[:,i], missing => 0) for i in 1:member_n)
member_vote_dict_missingn1 = Dict(member_vote_header[i] => replace(member_vote_arr[:,i], missing => -1) for i in 1:member_n)

# import member vote data (and fix "missing" -> missing)
committee_data_in = @_ readdlm(processed_committee_data_filepath, ',') |> replace(__, "missing" => missing)
committee_arr = committee_data_in[2:end,:]
committees = committee_data_in[1,:]
committee_n = length(committees)
committee_dict = Dict(committees[i] => committee_arr[:,i] for i in 1:committee_n)

bill_n = size(member_vote_arr,1)
@assert bill_n == size(committee_arr,1)

println("done.")



# List parties
parties = @_ map(_["party"], values(member_info_dict)) |> Set |> collect
MembersOfParty = party_ -> (@_ __["member_id"]) <-- @_ filter(_["party"] == party_, collect <| values <| member_info_dict)
members_by_party = Dict(party_ => MembersOfParty(party_) for party_ in parties)

MeanVotesOfMembersNoMissing = members_ -> collect(MeanNoMissing((@_ __[i]) <-- (@_ member_vote_dict[_] <-- members_)) for i in 1:bill_n)
MeanVotesOfMembersMissingZero = members_ -> collect(MeanMissingZero((@_ __[i]) <-- (@_ member_vote_dict[_] <-- members_)) for i in 1:bill_n)
MeanVotesOfMembersMissingN1 = members_ -> collect(MeanMissingN1((@_ __[i]) <-- (@_ member_vote_dict[_] <-- members_)) for i in 1:bill_n)

party_mean_votes_nomissing_dict = Dict(party_ => MeanVotesOfMembersNoMissing(MembersOfParty(party_)) for party_ in parties)
party_mean_votes_missingzero_dict = Dict(party_ => MeanVotesOfMembersMissingZero(MembersOfParty(party_)) for party_ in parties)
party_mean_votes_missingn1_dict = Dict(party_ => MeanVotesOfMembersMissingN1(MembersOfParty(party_)) for party_ in parties)

party_abs_votes_dict = Dict(party_ => (sign <-- party_mean_votes_nomissing_dict[party_]) for party_ in parties)




# difference of each member to their party
# TODO: come up with a score that weights by how many votes are shared (so that people with only a few votes don't unreasonably high scores)
#   Could potentially be Bayesian?
MemberPartyDifferenceNoMissing = (member_, party_) -> (member_vote_dict[member_] - party_mean_votes_nomissing_dict[party_]).^2 |> MeanNoMissing |> sqrt
MemberPartyDifferenceMissingZero = (member_, party_) -> (member_vote_dict_missingzero[member_] - party_mean_votes_missingzero_dict[party_]).^2 |> MeanMissingZero |> sqrt
MemberPartyDifferenceMissingN1 = (member_, party_) -> (member_vote_dict_missingn1[member_] - party_mean_votes_missingn1_dict[party_]).^2 |> MeanMissingN1 |> sqrt

diffs_by_member_nomissing = Dict(member_ =>
                      (
                       Dict(party_ => MemberPartyDifferenceNoMissing(member_, party_) for party_ in parties)
                      )
                      for member_ in members)

diffs_by_member_missingzero = Dict(member_ =>
                      (
                       Dict(party_ => MemberPartyDifferenceMissingZero(member_, party_) for party_ in parties)
                      )
                      for member_ in members)

diffs_by_member_missingn1 = Dict(member_ =>
                      (
                       Dict(party_ => MemberPartyDifferenceMissingN1(member_, party_) for party_ in parties)
                      )
                      for member_ in members)

# Other measures of party loyalty
#loyalty_by_vote_pct
MemberLoyaltyByPct = member_ -> (((party_abs_votes_dict[member_info_dict[member_]["party"]] - member_vote_dict[member_]) |> RemoveMissing) |> (@_ (count(x -> (abs(x) < 1E-8), __) / length(__))))
member_loyalty_by_pct = Dict{String, Union{Missing, Number}}(member_ => MemberLoyaltyByPct(member_) for member_ in members)

member_loyalty_by_diff_nomissing = Dict{String, Union{Missing, Number}}(member_ => 1 - 0.5*diffs_by_member_nomissing[member_][member_info_dict[member_]["party"]] for member_ in members)

# eliminate unaffiliated members ("무소속")
for member_ in members_by_party["무소속"]
    member_loyalty_by_pct[member_] = missing
    member_loyalty_by_diff_nomissing[member_] = missing
end


# Absentee rates
MissingPercent = vec_ -> 1 - ( length(vec_ |> RemoveMissing) / length(vec_) )

# member_absenteeism = Dict(member_ => member_vote_dict[member_] |> (@_ 1 - (length(__ |> RemoveMissing) / length(__))) for member_ in members)
member_absenteeism = Dict(member_ => member_vote_dict[member_] |> MissingPercent for member_ in members)

# absenteeism by committee
MemberVoteCommitteeSubset = (member_, committee_) -> ( @_ _[1] <-- filter(x -> x[2]==1, collect <| zip(member_vote_dict[member_], committee_dict[committee_])) )
member_absenteeism_by_committee = Dict(member_ =>
   Dict(committee_ =>
        MemberVoteCommitteeSubset(member_, committee_) |> MissingPercent
        for committee_ in committees
       )
   for member_ in members)



# ages
member_ages = Dict(member_ => AgeFromDOB(member_info_dict[member_]["dob"]) for member_ in members)
