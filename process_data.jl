import JSON
using DelimitedFiles
include("shortcuts.jl")

session = 21


scrape_data_dir = "../SKNABillVoteData/data/"
bill_subdir = "bills"
member_info_filename = "member_info_data_session$(session).json"

processed_data_dir = "data/"
processed_bill_data_filename = "bill_data_session$(session).json"
processed_member_data_filename = "member_vote_data_session$(session).csv"
processed_committee_data_filename = "committee_bill_data_session$(session).csv"




# build filepaths
member_info_filepath = joinpath(scrape_data_dir, member_info_filename)
bill_dir = joinpath(scrape_data_dir, bill_subdir)
processed_bill_data_filepath = joinpath(processed_data_dir, processed_bill_data_filename)
processed_member_data_filepath = joinpath(processed_data_dir, processed_member_data_filename)
processed_committee_data_filepath = joinpath(processed_data_dir, processed_committee_data_filename)


# import member list
print("Reading member list...")
@assert(isfile(member_info_filepath))
member_info_json = open(member_info_filepath) do f
    read(f, String)
end
member_info_dict = JSON.parse(member_info_json)
println("done.")

# import bill data
bill_filenames = readdir(bill_dir)
bill_filenames = filter(x -> match(Regex("session$session"), x) |> !isnothing, bill_filenames)


# # DEBUG: only do 10 bills
# bill_filenames = bill_filenames[1:10]


bill_filepaths = map(x -> joinpath(bill_dir, x), bill_filenames)



# construct set of all bills

print("Reading bills...")
bill_dicts = []
for this_bill_filepath in bill_filepaths
    @assert(isfile(this_bill_filepath))
    this_bill_json = open(this_bill_filepath) do f
        read(f, String)
    end
    this_bill_dict= JSON.parse(this_bill_json)
    push!(bill_dicts, this_bill_dict)
end
println("done.")

# construct stripped-down version of bill_dicts without vote data, for saving to json
bill_dicts_lite = deepcopy(bill_dicts)
keys_to_delete = ["members_agree", "members_oppose", "members_abstain", "summary"]
for k in keys_to_delete
    @_ delete!(_, k) <-- bill_dicts_lite
end



# for each member, construct a vector of votes: 1 for yes, -1 for no, 0 for abstain, missing for not present

MemberAgreeOnBill = (member_id_, bill_dict_) -> reduce(|, map(x -> x["member_id"] == member_id_, bill_dict_["members_agree"]), init=false)
MemberOpposeOnBill = (member_id_, bill_dict_) -> reduce(|, map(x -> x["member_id"] == member_id_, bill_dict_["members_oppose"]), init=false)
MemberAbstainOnBill = (member_id_, bill_dict_) -> reduce(|, map(x -> x["member_id"] == member_id_, bill_dict_["members_abstain"]), init=false)

MemberAgreeVoteList = member_id_ -> map(x -> MemberAgreeOnBill(member_id_, x), bill_dicts)
MemberOpposeVoteList = member_id_ -> map(x -> MemberOpposeOnBill(member_id_, x), bill_dicts)
MemberAbstainVoteList = member_id_ -> map(x -> MemberAbstainOnBill(member_id_, x), bill_dicts)

MemberVoteList = member_id_ -> begin
    member_agree_vote_list = MemberAgreeVoteList(member_id_)
    member_oppose_vote_list = MemberOpposeVoteList(member_id_)
    member_abstain_vote_list = MemberAbstainVoteList(member_id_)

    # ensure vote lists are exclusive
    @assert(all(x -> x == 0, member_agree_vote_list   .& member_oppose_vote_list))
    @assert(all(x -> x == 0, member_oppose_vote_list  .& member_abstain_vote_list))
    @assert(all(x -> x == 0, member_abstain_vote_list .& member_agree_vote_list))

    member_skip_vote_list = map(!, (member_agree_vote_list[i] || member_oppose_vote_list[i] || member_abstain_vote_list[i]) for i in 1:length(member_agree_vote_list))

    map(x -> x ?   1 : 0, member_agree_vote_list) +
    map(x -> x ?  -1 : 0, member_oppose_vote_list) +
    map(x -> x ?   0 : 0, member_abstain_vote_list) +
    map(x -> x ? missing : 0, member_skip_vote_list)
end

print("Building member vote lists...")
member_vote_lists_dict = Dict( member_id_ => MemberVoteList(member_id_) for member_id_ in keys(member_info_dict))
println("done")




print("Building committee bill lists...")
# Construct lists for committees
committees = Set(map(x -> x["committee"], bill_dicts))
CommitteeBillList = committee_ -> map(x -> x["committee"] == committee_, bill_dicts)
committee_bill_lists_dict = Dict( committee_ => CommitteeBillList(committee_) for committee_ in committees)
println("done")


# Save results to csv files
# Note: I originally wanted to save the bill ids to the first column, but that's
# just too complicated. We don't really need them anyway. If we want to do more
# bill processing (e.g., NLP), we should be doing it above here anyway.

# create processed data dir if it doesn't exist
if ~isdir(processed_data_dir)
    mkdir(processed_data_dir)
end

member_data_header = collect(keys(member_vote_lists_dict))
member_data_header = reshape(member_data_header, 1, length(member_data_header))
member_data_arr = reduce(hcat, values(member_vote_lists_dict))

committee_data_header = collect(keys(committee_bill_lists_dict))
committee_data_header = reshape(committee_data_header, 1, length(committee_data_header))
committee_data_arr = map(Int, reduce(hcat, values(committee_bill_lists_dict)))

print("Writing data...")
writedlm(processed_member_data_filepath, [member_data_header; member_data_arr], ",")
writedlm(processed_committee_data_filepath, [committee_data_header; committee_data_arr], ",")

# write bill data
open(processed_bill_data_filepath,"w") do f
    JSON.print(f, bill_dicts_lite, 4)
end
println("done")
