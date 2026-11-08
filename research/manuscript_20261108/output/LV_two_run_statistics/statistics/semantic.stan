
data {int<lower=1> N; int<lower=1> C; int<lower=1> B; int<lower=1> A; int<lower=1> W; int<lower=1> I; int<lower=1> K; array[N] int<lower=0,upper=1> y; array[N] int<lower=1,upper=C> cell; array[N] int<lower=1,upper=B> block; array[N] int<lower=1,upper=A> agent; array[N] int<lower=1,upper=W> word; array[N] int<lower=1,upper=I> item; array[N] int<lower=1,upper=K> case_id; array[N] int<lower=0,upper=1> use_state; real<lower=0> beta_scale; real<lower=0> sd_scale;}
parameters {vector[C] beta; vector[B] z_block; vector[A] z_agent; vector[W] z_word; vector[I] z_item; vector[K] z_case; vector[B] z_block_slope; vector[W] z_word_slope; vector<lower=0>[7] sd;}
transformed parameters {vector[N] eta; for(n in 1:N) eta[n]=beta[cell[n]]+sd[1]*z_block[block[n]]+sd[2]*z_agent[agent[n]]+sd[3]*z_word[word[n]]+sd[4]*z_item[item[n]]+sd[5]*z_case[case_id[n]]+use_state[n]*(sd[6]*z_block_slope[block[n]]+sd[7]*z_word_slope[word[n]]);}
model {beta ~ normal(1.5,beta_scale); z_block ~ std_normal(); z_agent ~ std_normal(); z_word ~ std_normal(); z_item ~ std_normal(); z_case ~ std_normal(); z_block_slope ~ std_normal(); z_word_slope ~ std_normal(); sd ~ normal(0,sd_scale); y ~ bernoulli_logit(eta);}
generated quantities {array[N] int y_rep; vector[N] log_lik; for(n in 1:N) {y_rep[n]=bernoulli_logit_rng(eta[n]); log_lik[n]=bernoulli_logit_lpmf(y[n]|eta[n]);}}

