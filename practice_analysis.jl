# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,jl:percent
#     text_representation:
#       extension: .jl
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.3
#   kernelspec:
#     display_name: Julia 1.6.2
#     language: julia
#     name: julia-1.6
# ---

# %%
include("shortcuts.jl")

#import Pkg;

#Pkg.add("Plots")
ENV["GKS_ENCODING"] = "utf-8"
using Plots

#Pkg.add("MultivariateStats")
#using MultivariateStats

using LinearAlgebra

import JSON

# %%
include("analyses.jl")

# %%
# TODO: OUTPUT BILL DATA IN process_data.jl
#       so that we don't have to reread all the bills here, and we don't make an ordering error.

processed_bill_data_filename = "bill_data_session$(session).json"
processed_bill_data_filepath = joinpath(processed_data_dir, processed_bill_data_filename)

bill_data_json = open(processed_bill_data_filepath) do f
        read(f, String)
end
bill_dicts = JSON.parse(bill_data_json)

# %%
filter(x -> contains(x["name"],"부"), member_info_dict |> values |> collect)

# %%
primemin_id_1 = "9771106"
#primemin_id_2 = ... # Kim Boo-kyum is not an assembly member??

# %%
members_by_party[parties[1]]

# %%
party_diff_j=3;

partyi=1;
plot_s1 = scatter((@_ (diffs_by_member[_][parties[party_diff_j]]) <-- members_by_party[parties[partyi]]) |> sort, label=parties[partyi], titlefont=font(11, "Helvetica"), legendfont=font(9, "Helvetica"), title="Diff from "*parties[party_diff_j])
for partyi in 2:length(parties)
    scatter!(plot_s1, (@_ (diffs_by_member[_][parties[party_diff_j]]) <-- members_by_party[parties[partyi]]) |> sort, label=parties[partyi], legendfont=font(9, "Helvetica"))
end
plot_s1

# %% tags=[]
# Lee Nak-yeon
diffs_by_member[primemin_id_1]["더불어민주당"]

# %%
party_diff_j=2;

partyi=1;
plot_s1 = scatter((@_ (diffs_by_member[_][parties[party_diff_j]]) <-- members_by_party[parties[partyi]]) |> sort, label=parties[partyi], titlefont=font(11, "Helvetica"), legendfont=font(9, "Helvetica"), title="Diff from "*parties[party_diff_j])
for partyi in 2:length(parties)
    scatter!(plot_s1, (@_ (diffs_by_member[_][parties[party_diff_j]]) <-- members_by_party[parties[partyi]]) |> sort, label=parties[partyi], legendfont=font(9, "Helvetica"))
end
plot_s1

# %%
party_diff_j=7;

partyi=1;
plot_s1 = scatter((@_ (diffs_by_member[_][parties[party_diff_j]]) <-- members_by_party[parties[partyi]]) |> sort, label=parties[partyi], titlefont=font(11, "Helvetica"), legendfont=font(9, "Helvetica"), title="Diff from "*parties[party_diff_j])
for partyi in 2:length(parties)
    scatter!(plot_s1, (@_ (diffs_by_member[_][parties[party_diff_j]]) <-- members_by_party[parties[partyi]]) |> sort, label=parties[partyi], legendfont=font(9, "Helvetica"))
end
plot_s1

# %%
# mean diffs by party
diffs_by_party = Dict{String,Dict}()
for this_party_1 in parties
    diffs_by_party[this_party_1] = Dict{String,Number}()
    for this_party_2 in parties
        diffs_by_party[this_party_1][this_party_2] = (@_ (diffs_by_member[_][this_party_2]) <-- members_by_party[this_party_1]) |> mean
    end
end

# %%
diffs_by_party

# %%
party_diff_j=3;

diffs_by_party[parties[party_diff_j]] |> (x -> [[x[k], k] for k in keys(x)]) |> sort |> @_ bar([x[2] for x in __], [x[1] for x in __],orientation=:h, titlefont=font(11, "Helvetica"), ytickfont=font(9, "Helvetica"), legendfont=font(9, "Helvetica"), title="Diff from "*parties[party_diff_j],label=false)

# %%
party_diff_j=2;

diffs_by_party[parties[party_diff_j]] |> (x -> [[x[k], k] for k in keys(x)]) |> sort |> @_ bar([x[2] for x in __], [x[1] for x in __],orientation=:h, titlefont=font(11, "Helvetica"), ytickfont=font(9, "Helvetica"), legendfont=font(9, "Helvetica"), title="Diff from "*parties[party_diff_j],label=false)

# %%
party_diff_j=7;

diffs_by_party[parties[party_diff_j]] |> (x -> [[x[k], k] for k in keys(x)]) |> sort |> @_ bar([x[2] for x in __], [x[1] for x in __],orientation=:h, titlefont=font(11, "Helvetica"), ytickfont=font(9, "Helvetica"), legendfont=font(9, "Helvetica"), title="Diff from "*parties[party_diff_j],label=false)

# %%
# TODO: PCA

# %%
member_vote_arr_nomissing =  convert(Matrix{Number},replace(member_vote_arr, missing => 0));

# %%
U,S,V=svd(member_vote_arr_nomissing);

# %%
# single-member json example
# TODO: include party support for each bill, so we can highlight if a given member opposed their own party

# we want to just make a list of lists:
#  [date, member support, overall result, bill name, bill committee, member party support (if not indep)]

# %%
this_member="9770869"
this_member_party = member_info_dict[this_member]["party"]

# %%
this_member_votes = member_vote_dict[this_member]
this_party_votes = sign <-- party_mean_votes_dict[this_member_party]

# %%
this_member_bill_data = [
[
bill_dicts[j]["vote_date"],
this_member_votes[j],
bill_dicts[j]["result"],
bill_dicts[j]["name"],
bill_dicts[j]["committee"],
this_party_votes[j]
]
    for j in 1:length(this_member_votes)
        ]

# %%
# Try to figure out how "more loyal" party members vote depending on how the rest of the party votes...

# %%
members_by_party["국민의힘"]
[ ((filter(x -> ismissing(x), member_vote_dict[id]) |> length),id) for id in members_by_party["국민의힘"] ] |> sort

# %%
this_member="9770837"
this_member_party = member_info_dict[this_member]["party"]
party_mean_votes_dict[this_member_party] |> sort
filter(x -> ismissing(x), member_vote_dict[this_member]) |> length

# %%
# TODO: make bins and compute how often this_member votes yes for each bin
histogram(filter(x-> (~ismissing(x)),party_mean_votes_dict[this_member_party]),bins=:scott)

# %%
# Output eample member data JSON

# %%
this_filename = "example_member_data_" * this_member * ".json"

# %%
open(this_filename,"w") do f
    JSON.print(f, Dict(["data"=>this_member_bill_data]))
end
