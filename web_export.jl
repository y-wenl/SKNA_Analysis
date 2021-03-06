import JSON

data_super_dir = "../data/"

output_data_dir = joinpath(data_super_dir, "webdata/")
output_member_data_dir = joinpath(output_data_dir, "members/")
member_vote_filename_base = "member_vote_data_SESSION_ID.json"
member_list_filename_base = "members_data_SESSION.json"

processed_data_dir = joinpath(data_super_dir, "processed/")
members_fullinfo_filename_base = "members_fullinfo_sessionSESSION.json"

session = 21

# Run analyses.jl first
include("analyses.jl")


# create directories if necessary
if ~isdir(output_data_dir)
    mkdir(output_data_dir)
end
if ~isdir(output_member_data_dir)
    mkdir(output_member_data_dir)
end

member_loyalty = member_loyalty_by_diff_nomissing


# Add age, and loyalty and absenteeism values and ranks to member_info
# Then export as json
members_fullinfo_filename = replace(members_fullinfo_filename_base, "SESSION" => session)
members_fullinfo_filepath = joinpath(processed_data_dir, members_fullinfo_filename)
for member_ in members
    party_ = member_info_dict[member_]["party"]

    member_info_dict[member_]["age"]          = member_ages[member_]
    member_info_dict[member_]["absenteeism"]  = member_absenteeism[member_]
    member_info_dict[member_]["loyalty"]      = member_loyalty[member_]

    member_info_dict[member_]["partysize"]    = length(members_by_party[party_])
    member_info_dict[member_]["totalmembers"] = length(members)

    # compute ranks
    this_absenteeism = member_absenteeism[member_]
    if ismissing(this_absenteeism)
        absenteeism_rank = missing
        absenteeism_party_rank = missing
    else
        all_absenteeism = @_ [member_absenteeism[member2_] for member2_ in members] |> replace(__, missing => 0)
        party_absenteeism = @_ [member_absenteeism[member2_] for member2_ in members_by_party[party_]] |> replace(__, missing => 0)

        absenteeism_rank = length(filter(x -> x > this_absenteeism, all_absenteeism)) + 1
        absenteeism_party_rank = length(filter(x -> x > this_absenteeism, party_absenteeism)) + 1
    end
    member_info_dict[member_]["absenteeism_rank"] = absenteeism_rank
    member_info_dict[member_]["absenteeism_party_rank"] = absenteeism_party_rank

    this_loyalty = member_loyalty[member_]
    if ismissing(this_loyalty)
        loyalty_rank = missing
        loyalty_party_rank = missing
    else
        all_loyalty = @_ [member_loyalty[member2_] for member2_ in members] |> replace(__, missing => 99)
        party_loyalty = @_ [member_loyalty[member2_] for member2_ in members_by_party[party_]] |> replace(__, missing => 99)

        loyalty_rank = length(filter(x -> x > this_loyalty, all_loyalty)) + 1
        loyalty_party_rank = length(filter(x -> x > this_loyalty, party_loyalty)) + 1
    end
    member_info_dict[member_]["loyalty_rank"] = loyalty_rank
    member_info_dict[member_]["loyalty_party_rank"] = loyalty_party_rank

end

# write to json
open(members_fullinfo_filepath,"w") do f
    JSON.print(f, member_info_dict, 0)
end

# export list of members
# name, party, region, age, [TODO gender], terms in office, absenteeism, party loyalty, committee membership
member_list_filename = replace(member_list_filename_base, "SESSION" => session)
member_list_filepath = joinpath(output_data_dir, member_list_filename)
member_list_header = [
                      "member_id",
                      "name",
                      "party",
                      "district",
                      "age",
                      "terms",
                      "absenteeism",
                      "loyalty",
                      "committees",
                     ]
member_list_data = [
                         [
                          member_,
                          member_info_dict[member_]["name"],
                          member_info_dict[member_]["party"],
                          member_info_dict[member_]["district"],
                          member_ages[member_],
                          member_info_dict[member_]["terms"],
                          member_absenteeism[member_],
                          member_loyalty[member_],
                          join(member_info_dict[member_]["committees"], ", "),
                         ]
                         for member_ in members
                        ]
@assert(length(member_list_header) == length(member_list_data[1]))
open(member_list_filepath,"w") do f
    JSON.print(f, Dict(["header"=>member_list_header, "data"=>member_list_data]), 0)
end


# export each member's bill list
print("Saving individual member data...")
for this_member in members
    this_filename = replace(member_vote_filename_base, "ID" => this_member)
    this_filename = replace(this_filename, "SESSION" => session)
    this_filepath = joinpath(output_member_data_dir, this_filename)

    this_member_party = member_info_dict[this_member]["party"]

    this_member_votes = member_vote_dict_with_ignores[this_member]
    this_member_vote_indices = findall(x -> ismissing(x) || (x != "ignore"), this_member_votes)

    this_party_votes = party_abs_votes_dict[this_member_party]

    this_member_bill_header = [
                          "date",
                          "member_vote",
                          "party_vote",
                          "result",
                          "name",
                          "committee",
                          "bill_id",
                          "bill_no",
                          "id_master",
                         ]
    this_member_bill_data = [
                             [
                              bill_dicts[j]["vote_date"],
                              this_member_votes[j],
                              this_party_votes[j],
                              bill_dicts[j]["result"],
                              bill_dicts[j]["name"],
                              bill_dicts[j]["committee"],
                              bill_dicts[j]["bill_id"],
                              bill_dicts[j]["bill_no"],
                              bill_dicts[j]["id_master"],
                             ]
                             for j in this_member_vote_indices
                            ]
    @assert(length(this_member_bill_header) == length(this_member_bill_data[1]))
    open(this_filepath,"w") do f
        JSON.print(f, Dict(["header"=>this_member_bill_header, "data"=>this_member_bill_data]), 0)
    end
end
print("done\n")
