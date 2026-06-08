Project ideas for improving LLMs' conceptual reasoning
We have a bunch of projects for improving LLMs' conceptual reasoning ability that we are excited to collaborate on. We are also excited about being pitched projects.
You can also check out our previous project in the area which we're planning to properly launch soon: A dataset of rated conceptual arguments

Project list
Make a big set of interesting prompts/tasks/questions (without answers)
Train on our consistency dataset
Use our consistency dataset to build a search-by-contradiction pipeline
Contribute to a conceptual creativity dataset
Fiddle with Claude Code to automatically turn insightful (conceptual) texts into hard (conceptual) questions  (with answers)
Train AIs to imitate particular people (or at least know what their views are/would be)
“Critical points text prediction”
Create alignment data for LMCA
More projects we're happy to collaborate on
Small projects (<7 days)
Specifically acausal projects

Make a big set of interesting prompts/tasks/questions (without answers)
Description:
"Interesting" in this case just means: Things we would actually like models to be good at doing or answering.
One approach would be to spend a lot of time hand-generating high-quality prompts/tasks/questions. Another approach would be just scraping them from AI safety blogposts etc. We could also ask people working on conceptual tasks with LLMs for their claude.ai or Claude Code data (or make a tool so they can easily send it to us.
Motivation: The idea here is that, for example, Anthropic could get Mythos to answer these questions and then distill the reasoning and answers into Opus. And so on for other companies and future unreleased-released model pairs.
Owner: By default, we'll do at least some of this by starting to collect people's conceptual Claude (code) conversations. But if you're excited about this, you could own this.
Duration: The MVP here just takes a couple of days. An ambitious version could take weeks.
Train on our consistency dataset
Description:
We have a big dataset for measuring how consistent models are along various axes in philosophical domains.
For example:
Questions for asking the models for:
P(CDT), P(CDT | libertarian free will), P(libertarian free will), P(CDT | no libertarian free will), P(no libertarian free will)
Then associate with these prompts the constraint:
P(CDT) = P(CDT | libertarian free will) * P(libertarian free will) + P(CDT | no libertarian free will) * P(no libertarian free will)
(Though most of our constraints are more "in the weeds" than this.)
We can now try to train models to be more consistent using this dataset and then check whether this improves their conceptual reasoning capabilities.
It’s worth noting that there are other ways to get improvements. E.g., instead of directly training models to satisfy constraints. The models could reflect on the consistency violations and decide how to change their behavior.
We expect there to be some tricky obstacles to training.
We've done some simple de-risking for training and checked whether consistency correlates with generic model competence. It turns out that the answer is only “yes” for some constraint types. For some constraint classes, the correlation is quite murky. From what we can tell, the problem is that more competent models tend to assign more extreme probabilities and also update more – i.e., their conditional probabilities P(A|B) and P(A|~B) deviate more from their priors (P(A)). Both of these properties make them less consistent by natural measures of consistency.
We worry that it might be difficult to get training on consistency to work. For instance, one probably has to think very carefully about what loss function to use to avoid models improving consistency scores in spurious/uninteresting ways (most obviously, by doing things like assigning less extreme probabilities in general). It might also be hard to see a strong effect on relevant capabilities since consistency seems like a very indirect measure.
Motivation: Consistency datasets are very scalable, so it would be great if it turns out that consistency training (in the domains we care about) helps with capabilities (we care about).
Owner: We're not planning to work on this ourselves but are happy to supervise somebody on this project
Duration: Depends on how fast we see progress, but likely a month or longer
Use our consistency dataset to build a search-by-contradiction pipeline
Description:
Develop a technique that models can use to find arguments at inference time to improve their conceptual reasoning. To explain:
One can view consistency as a way to find conceptual arguments that the model believes, but which it does not by default believe the conclusion of. E.g., the constraint P(A)>=P(A|B)P(B) can be viewed as an argument with premises “probably B” and “if B, then probably A” and conclusion “probably A”. If you violate this constraint, it means that you agree (in some sense) with “probably B” and “if B, then probably A” but disagree with “probably A”.
We could then get models to use consistency as a technique to find arguments that they can use to better reason through conceptual reasoning problems. E.g., they want to reason about proposition A. By finding inconsistencies like the above involving A, they can find arguments for or against A that they don't by default integrate into their reasoning about A, which they might want to research further, etc.
Motivation:
Owner: We're not planning to work on this ourselves but are happy to supervise somebody on this project
Duration:

Contribute to a conceptual creativity dataset
Caspar already started a bit of work on this project and would lead. You could contribute by writing data points on topics of your expertise, likely within AI alignment or control. (Each data point is extremely laborious.)

Detailed description (copied from https://docs.google.com/document/d/1FdKdLEpQ_QlWzd-MUe9crMS2olYYij-FWC0tVRxv9m8/):
The primary dataset
Here’s what the main dataset would look like:
There are tasks/questions, e.g., “propose a desirable property of voting rules” or “make an argument for CDT”, or “propose an alignment agenda”, or maybe “come up with a crucial consideration for altruists”. (The real task descriptions would be longer.)
For each task/question, there’s a list of distinct, high-quality answers, e.g., “a voting rule should be monotonic”, “it should be NP-hard to compute optimal manipulations”. (The real answers would be longer, more precise.)

The dataset induces the generative task of coming up with a new answer, given (a subset of) this list of existing answers. By varying the number of existing answers to put in the prompt we vary the difficulty of the generative task. Of course, to use the dataset as an eval, the new answer has to then be evaluated in some way, see below.

Why I think this is a good idea:
Creativity is usually not the models' strong suit. Also, coming up with new ideas on some of these tasks is difficult for humans and often takes a lot of work. So probably models will have bad performance on this. (From preliminary exploration, the models are indeed very bad at this.)
Humans would primarily have to generate tasks. Answers can be generated in part by models.
Excitingly, the difficulty of the generation task automatically grows as models become more capable because one can simply add the models’ latest ideas to the dataset. This also means that the dataset can scale relatively easily beyond human capabilities.
Perhaps even more so than our argumentation dataset, this is fairly close to being immediately useful. E.g., if the model generated interesting new arguments for EDT (or UDT and perhaps even CDT), I’d probably write them up into blog posts.
A secondary dataset: rated model responses to tasks
I think there should also be a second dataset with rated model responses to tasks.

Each entry of this dataset would consist of the following item:
A task (from the main dataset)
Some existing solutions to the task (from the main dataset)
A model’s proposed new solution to the task
A human rating of the model’s solution

Why have this dataset? It’d be useful for the following:
You can use it for trying to train models to be better at coming up with ideas (by DPOing toward better responses or SFTing on good responses)
Presumably one will want to try to use models for evaluating (model-generated) solutions to tasks. A dataset of rated solutions will help evaluate and improve (e.g., by prompting) models’ ability to rate solutions to tasks.
Also, one would likely generate some such dataset anyway when generating and working with the primary dataset. E.g., even if we exclusively use the dataset as an eval and hand-rate model answers to see how good the models are (whether inference-scaling helps, whether Uncle Bob’s proposed scaffold works, etc.), we might as well save those ratings.
Fiddle with Claude Code to automatically turn insightful (conceptual) texts into hard (conceptual) questions  (with answers)
Description: Caspar and Alex will spend at least a few days fiddling with different approaches to this and you can join (requires you to come up with some ideas yourself). If it goes well, we'll take the best approach(es) and spend weeks/months to generate a nice dataset with them.
Example approach: There are some hard problems where LLMs just have the answer memorised. Instruct an LLM to incrementally remove/alter more and more context from the problem until LLMs can no longer solve the problem.
Train AIs to imitate particular people (or at least know what their views are/would be)
Description: Somewhat self-explanatory.
Motivation: The idea is that it's a great context to get training data because we have ground truth about what a particular person would say even in fuzzy conceptual domains where we don't have object-level ground truth.
Owner: By default, Caspar is planning to work on a closely related project, so you might want to work together and you definitely want to at least coordinate a bit.
“Critical points text prediction”
(Cf. “reinforcement pretraining” as discussed b y Dong et al.)
Description: Give models the first n pages of some text, for example a Philosophy paper, and ask the models to predict the semantic content of the remainder of the text. Could do variations where we instead remove content in the middle and so on.
This would naturally lead into a training project, though probably we’d just feed it into our existing training pipeline (“Project Puffin”) and see what happens.
Owner: Currently, nobody on our team is planning to work on this by default but I think Caspar is flirting with the idea and either way, we'd be happy to supervise/collaborate on the project.
Create alignment data for LMCA
Description: We created a conceptual reasoning dataset which has a lot of position texts, critiques of those position texts, and expert ratings of these critiques. Currently, the dataset mostly contains many data points about philosophy, other random topics,  some hundreds on decision theory, and some on alignment, control, AI risk and so on but fewer than we'd like. You could work on generating high-quality data points on these topics with our guidance. (Rating would by default be done by our team. If you are a good fit for it, this could also be one of your tasks.)
Motivation: Seems good as an eval and basis for training for models' ability to do and uplift important conceptual work like thinking about alignment and decision theory. The dataset is used a lot by Anthropic as an eval and they are currently trying to train based on it. We will also share with GDM and maybe OpenAI.
Owner: By default, we won't be working on this, so you would be the one driving this forward but it would be in somewhat close collaboration with us, especially early on when we'll likely spend more time reviewing and giving feedback on data points.
Duration: You can contribute any number of data points you want if you're a good fit, so this is flexible.
More projects we're happy to collaborate on
Some sort of scaffold that produces some specific type of object, such as useful papers/blog posts/decisions
This could then for example be used to train models to predict the outcome of this process
Some sort of conceptual capabilities project based on some standard method (e.g., RLAIF for conceptual tasks; scaling “Ralph loops” / iterative self-critiquing; other scaffolds)
Human-labelled CoTs (e.g., label where models first go wrong when reasoning on DTBench, LMCA, etc.)
I think this one has a particularly high bar in terms of how high your conceptual reasoning skill needs to be to do this. We'd be testing your fit initially.
Make a dataset of high-quality conceptual texts
Probably we will do some of this by default and you could contribute.
Datasets based on LW/Alignment Forum/EA Forum/Reddit (maybe also Goodreads book ratings?) → Good and bad texts with scores
I think Abhay already did some work on this. Maybe there's more work to do.
Prompt/train/eval models on coming up with a scenarios/thought experiments that simultaneously exhibit n different random features
Bounty website for hard conceptual tasks
Tasks that are hard but it's easy for models to tell that the person's rubric is in fact correct
We make an automatic leaderboard
We hand-check the best ones and give prize money
Small projects (<7 days)
Ask people to record their discussions and collect these recordings somewhere to turn into training data once we have good multimodal models (or good transcription)
Prompt/training/eval models on the task of predicting which prompts will work best on LMCA (etc)
BSBench for philosophy → Dataset where models have to classify text as bullshit or not
Alex already started exploring this
Specifically acausal projects
We are also working on a few specifically acausal projects (decision theory evals, decision theory model organisms and so on).

Projects we're currently planning to do here:
Em is planning to start some initial experiments to see how RLing models to be CDT-ish in certain settings generalises. We might do a large RL → CDT demo or invest more into AI decision theory model organisms.
We are tentatively planning to extend DTBench with questions about updatelessness.
We are planning to continue talking to AI labs about including decision theory and multi-agent guidance into their models spec or some other formal or informal policy and might work on evals accompanying these guidances.
We write blog posts, run reading groups, give talks and so on.
