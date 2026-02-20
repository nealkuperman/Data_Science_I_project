<center>
<h1>TO DO</h1>
</center>
</br>

# DB
- update source/load_team_box_score.py to account for pace and poss from the advanced box score csv. 
    - I pulled the advanced box scores after writing the load script. Need to update and put into db
- add pace and pos db team box score schema 

---

## Preprocessing
- remove cols from processed box_score_df that do not make sense. Creating some cols automatically like rolling avg of diff of win % or something that may not make a ton of sense. 
- add games last 5, games last 10