import JSON

output_data_dir = "webdata/"
output_member_data_dir = joinpath(output_data_dir, "members/")
member_data_filename_base = "member_vote_data_SESSION_ID.json"
member_list_filename_base = "members_data_SESSION.json"

session = 21

# Run analyses.jl first
include("analyses.jl")

# Then read bill data
processed_bill_data_filename = "bill_data_session$(session).json"
processed_bill_data_filepath = joinpath(processed_data_dir, processed_bill_data_filename)
bill_data_json = open(processed_bill_data_filepath) do f
        read(f, String)
end
bill_dicts = JSON.parse(bill_data_json)






# create directories if necessary
if ~isdir(output_data_dir)
    mkdir(output_data_dir)
end
if ~isdir(output_member_data_dir)
    mkdir(output_member_data_dir)
end

# export list of members
# name, party, region, age, [TODO gender], terms in office, absenteeism, party loyalty, committee membership
member_list_filename = replace(member_list_filename_base, "SESSION" => session)
member_list_filepath = joinpath(output_data_dir, member_list_filename)
member_list_data = [
                         [
                          member_info_dict[member_]["name"],
                          member_info_dict[member_]["party"],
                          member_info_dict[member_]["district"],
                          member_ages[member_],
                          member_info_dict[member_]["terms"],
                          member_absenteeism[member_],
                          member_loyalty_by_diff_nomissing[member_],
                          join(member_info_dict[member_]["committees"], ", "),
                         ]
                         for member_ in members
                        ]
open(member_list_filepath,"w") do f
    JSON.print(f, Dict(["data"=>member_list_data]))
end


# export each member's bill list
print("Saving individual member data...")
for this_member in members
    this_filename = replace(member_data_filename_base, "ID" => this_member)
    this_filename = replace(this_filename, "SESSION" => session)
    this_filepath = joinpath(output_member_data_dir, this_filename)

    this_member_party = member_info_dict[this_member]["party"]

    this_member_votes = member_vote_dict[this_member]
    this_party_votes = party_abs_votes_dict[this_member_party]

    this_member_bill_data = [
                             [
                              bill_dicts[j]["vote_date"],
                              this_member_votes[j],
                              this_party_votes[j],
                              bill_dicts[j]["result"],
                              bill_dicts[j]["name"],
                              bill_dicts[j]["committee"],
                             ]
                             for j in 1:length(this_member_votes)
                            ]
    open(this_filepath,"w") do f
        JSON.print(f, Dict(["data"=>this_member_bill_data]))
    end
end
print("done\n")
