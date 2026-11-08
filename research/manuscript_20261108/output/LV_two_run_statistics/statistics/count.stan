
data {int<lower=1> N; int<lower=1> C; int<lower=1> B; array[N] int<lower=0> y; array[N] int<lower=1,upper=C> cell; array[N] int<lower=1,upper=B> block; vector[N] log_messages; real<lower=0> beta_scale; real<lower=0> sd_scale; real<lower=0> shape_scale;}
parameters {vector[C] beta; vector[B] z_block; real<lower=0> sd_block; real log_shape;}
transformed parameters {vector[N] eta; real<lower=0> shape=exp(log_shape); for(n in 1:N) eta[n]=log_messages[n]+beta[cell[n]]+sd_block*z_block[block[n]];}
model {beta ~ normal(-2.5,beta_scale); z_block ~ std_normal(); sd_block ~ normal(0,sd_scale); log_shape ~ normal(log(10),shape_scale); y ~ neg_binomial_2_log(eta,shape);}
generated quantities {array[N] int y_rep; vector[N] log_lik; for(n in 1:N) {y_rep[n]=neg_binomial_2_log_rng(eta[n],shape); log_lik[n]=neg_binomial_2_log_lpmf(y[n]|eta[n],shape);}}

