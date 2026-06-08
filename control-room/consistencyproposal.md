Consistency Training
Apr 28, 2026 Caspar Oesterheld, Emery Cooper, Chi Nguyen

In a lot of important domains we care about (alignment, ethics, etc.), it’s hard to provide ground truth signals to train models against. (In many cases, the best we can do is provide best-guess human labels, but these are expensive and for a lot of claims we can’t be very confident in them.)

One interesting idea for addressing this is to use consistency as a loss function. Even in domains where we don’t know the answers (and can’t grade proposed answers) to most questions, we can still sometimes relate the answers to different questions. E.g., we know that P(A and B) has to be less than or equal to P(A), even if A and B are hard-to-assess claims, such as “insects are conscious” or “marginal AI safety dollars should be spent on control”.

We have done some preliminary work based on this idea – see below. In particular, we have a dataset of consistency constraints and some experimental results suggesting that training on consistency (and on these datasets in parti cular) might work.

The goal of the proposed project is to use this idea to train models to be more consistent and thereby make them better (including but not exclusively more consistent). For instance, you might train a small model to be more consistent and then check:
Does it get more consistent on the training/test set?
Do the responses qualitatively change (e.g., do the CoTs become longer)?
Does a bigger/frontier model prefer the responses of the trained model over responses of the untrained model?
Does the model get better on a dataset like LMCA?

We aren’t set on a specific method for training models to be consistent. But the simplest approach is to use regular RL methods (like GRPO) to train a model’s responses to one prompt to align more with the responses to another prompt (or set of prompts). For instance, if the model’s response to a prompt for P(A and B) gives a higher number on average than for P(A), then we’d train the model to give higher P(A) and lower P(A and B).

Note: It’s a bit unclear whether we’d want to publish the results of this project, given that training on consistency could be a useful trick for improving models at all kinds of tasks. If this is determinative for whether you’d like to work on this, let us know!
Preliminary work
We have done a bunch of preliminary work on this, but haven’t tried training.

We have a dataset of >10k consistency constraints on conceptual issues, i.e., sets of prompts asking the models to assign, for instance, probabilities, along with desiderata on the responses to these prompts. We also have a pipeline for generating more such data. You can use this for training if you like. (We also have a second dataset of 400 minor rewrites of critiques in the LMCA dataset.)

From our own experiments, it’s not that hard to find consistency constraints that models substantially violate. 

We have some preliminary experiments supporting the idea that this is feasible:
Better models are generally more consistent on both of the above datasets.
On the LMCA rewrites dataset, prompts that make models more consistent also tend to make them better at the LMCA task.
Among different responses by a weak model, a strong model tends to prefer the responses that are more consistent. For example, let’s say we ask the model the same probabilistic question with two different (but equivalent) prompts, X and Y, and get some number of samples each. Let’s say responses to Y are higher on average (so that it can be said that the model responds inconsistently to the two prompts). Then, empirically, among two randomly selected responses to Y, Opus 4.6 – asked to evaluate the response as a whole, including the CoT – will prefer the one that gives lower numbers more than 50% of the time. (Similarly, among responses to X, Opus 4.6 will prefer responses that give higher numbers more than 50% of the time.) This suggests that some versions of consistency training might have a similar effect to training against a much more powerful reward model.

