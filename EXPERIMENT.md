Question. Can prompt optimization (GEPA) significantly improve performance of a model on LMCA, using self reflection and human ratings (EC) as a signal for reward. 

Background. LMCA is a dataset of position texts and critiques. Each text has 1 or more critiques. Humans have rated these critiques from 0-1 based off a rubric. We can measure conceptual reasoning by having models rate these critiques and comparing them to the human ratings. 

Experiment Idea. 
The fundamental insight is to do a "repeat until convegence" technique. 

Consider a pair of critiques for a position text where the critique judge model and EC have strong disgreements. Show a reflector model (the same one) the pair, the EC score, and have it keep rewriting the prompt for the judge model until the judge model is able to properly rank the pair. We are using the weighted pairwise error metric from the LMCA paper. 

Once the judge model is correctly ranking with the new prompt, take this prompt and check it on a random sample of questions where the judge model was already doing well for the previous prompt. Make sure there are no egregious regressions. 

Examples of things the reflector would want to add to the judge's prompt. 
- General rules of how to reason given something you see in the question 
- In context, few shot summarized examples with argument, critique, and proper rating 
- Vital background information the model doesn't already have, for topics like decision theory etc. I don't know if the reflector model will be capable of adding this information given it is the same model. I may allow web search for the reflector model, but this will be ablated. 

Actual Algorithm. 

Dataset. 
Take all the position texts from LMCA that have 1 or more critiques. There should be 180. Do a 60/40 train test split, because we have so little data we need a large enough test set to show our method actually works. Consider the actual topics of the position texts and make sure the distirbutions of the train and test set match. 

Use model gpt 5.4 nano with low effort for the critique judge model, medium effort for the reflector model. Use the OPENROUTER API key. For the initial prompt, use the prompt in base.txt (but clean up the formatting slgihtly). Call this P0; the pool starts as {P0}.

Do everything with the highest possibel concurrency. 

1. On train, using k = 3 (not sure how sensntive ratings rankings are to k)

Do a full judging run through the LMCA train set, repeating rankings from the judge for each critiques k times and avg the score on each critique. 

2. Measure weighted pairwise ranking error per position (this per-position error vector is what Pareto selection uses below). We are going to filter each pair into 3 categories: 
a. significant misrank (judge ranks the pair opposite to EC, EC overall-score gap >= 0.3) b. minor misrank 3. good ranking (0 error)

Objective: generally minimize weighted pairwise ranking error, but specificially end when all/most significant misranks are eliminated in the train set. We aren't too worried about minor miranks or if some questions regress into minor misranks, becuase significant misranks contribute most of the error. 

3. Repeat until the rollout budget B is exhausted. Each iteration is ONE select-then-fix step (the unit that repeats is the iteration, NOT the misrank list):
- Pareto-select a prompt P from the pool: for each position, the prompt with the lowest error wins it (count a win only if it beats the runner-up by more than epsilon = the metric's CI half-width, else treat as a tie). The frontier is every prompt that wins >= 1 position. Sample P from the frontier, weighted by number of positions won.
- Take ONE of P's significant misranks. Take COT + response (with rating) for both critiques, show to reflector with the correct human rankings and scores. 
- Get a new prompt from the reflector 
- Re-run the judge on this pair with the new prompt; if it still misranks, send it back to the reflector. Repeat until the pair is ranked correctly or you hit the budget of N = 6. 
- Add the resulting prompt to a pool (keep the parent prompt too, don't replace it).
- Regression test: re-run the judge with the new prompt on the ENTIRE train set at k = 3, recording its per-position error vector. The test fails if the new prompt's average train error exceeds the parent's by more than epsilon. 
- If the regression test fails, show prompt and the positions it regressed on to the reflector model, and have it rewrite to avoid regression while maintaining correctness on the original significant misrank. 
- Keep both the new prompt and the original prompt in the pool regardless, so Pareto selection (not patching) handles tradeoffs across positions.

4. After the loop ends (budget B exhausted), return the single pool prompt with the lowest AGGREGATE pairwise ranking error on train (k = 3), not the frontier. We should have significantly less pairwise ranking error than P0. Then run that prompt on test once, and compare against P0 on test, both with k = 3.
