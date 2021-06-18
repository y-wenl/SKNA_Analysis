import JSON


session = 21


data_dir = "../SKNABillVoteData/data/"
bill_subdir = "bills"
member_info_filename = "member_info_data_session$(session).json"

member_info_filepath = joinpath(data_dir, member_info_filename)
bill_dir = joinpath(data_dir, bill_subdir)



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


# DEBUG: only do 10 bills
bill_filenames = bill_filenames[1:10]


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




# for each member, construct a vector of votes: 1 for yes, -1 for no, 0 for abstain, NaN for not present

member_agree_on_bill_f = (member_id_, bill_dict_) -> reduce(|, map(x -> x["member_id"] == member_id_, bill_dict_["members_agree"]), init=false)
member_oppose_on_bill_f = (member_id_, bill_dict_) -> reduce(|, map(x -> x["member_id"] == member_id_, bill_dict_["members_oppose"]), init=false)
member_abstain_on_bill_f = (member_id_, bill_dict_) -> reduce(|, map(x -> x["member_id"] == member_id_, bill_dict_["members_abstain"]), init=false)

member_agree_vote_list_f = member_id_ -> map(x -> member_agree_on_bill_f(member_id_, x), bill_dicts)
member_oppose_vote_list_f = member_id_ -> map(x -> member_oppose_on_bill_f(member_id_, x), bill_dicts)
member_abstain_vote_list_f = member_id_ -> map(x -> member_abstain_on_bill_f(member_id_, x), bill_dicts)

member_vote_list_f = member_id_ -> begin
    member_agree_vote_list = member_agree_vote_list_f(member_id_)
    member_oppose_vote_list = member_oppose_vote_list_f(member_id_)
    member_abstain_vote_list = member_abstain_vote_list_f(member_id_)

    # ensure vote lists are exclusive
    @assert(all(x -> x == 0, member_agree_vote_list   .& member_oppose_vote_list))
    @assert(all(x -> x == 0, member_oppose_vote_list  .& member_abstain_vote_list))
    @assert(all(x -> x == 0, member_abstain_vote_list .& member_agree_vote_list))

    member_skip_vote_list = map(!, (member_agree_vote_list[i] || member_oppose_vote_list[i] || member_abstain_vote_list[i]) for i in 1:length(member_agree_vote_list))

    map(x -> x ?   1 : 0, member_agree_vote_list) +
    map(x -> x ?  -1 : 0, member_oppose_vote_list) +
    map(x -> x ?   0 : 0, member_abstain_vote_list) +
    map(x -> x ? NaN : 0, member_skip_vote_list)
end

print("Building member vote lists...")
member_vote_lists_dict = Dict( member_id_ => member_vote_list_f(member_id_) for member_id_ in keys(member_info_dict))
println("done")




print("Building committee bill lists...")
# Construct lists for committees
committees = Set(map(x -> x["committee"], bill_dicts))
committee_bill_list_f = committee_ -> map(x -> x["committee"] == committee_, bill_dicts)
committee_bill_lists_dict = Dict( committee_ => committee_bill_list_f(committee_) for committee_ in committees)
println("done")
