Objective: Verify that consistency training is equivalent to training on a more powerful reward model. 

Method: 
On my local gpu, use a Qwen 4B model. Generate a list of 50 type 1 and 50 type 2 questions/phrasings using a claude code file. Sample x amount of rollouts with the Qwen 4B model, rollouts with a full chain of thought. 

For each rollout, score the reward using the reward equation we developed in the experimental design. Then, using a very strong model (Opus 4.8 Extra High in Claude Code), using I guess pairwise comparison (But maybe another comparison is better), score the quality of the reasoning with the strong model. Then, compare the reward given by our reward equation with the evaluation by a strong model, and correlate them. 

