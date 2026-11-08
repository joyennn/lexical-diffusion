library(cmdstanr)
library(posterior)
library(jsonlite)
root <- normalizePath('output/LV_two_run_statistics')
dir.create(file.path(root,'statistics'), showWarnings=FALSE)
out <- file.path(root,'statistics')
d <- read.csv('replication_check/analysis/run_metrics.csv')
d <- d[d$group=='nonseed' & ((d$start_cycle==1 & d$end_cycle==100 & d$condition!='time200') | (d$start_cycle==101 & d$end_cycle==200 & d$condition=='time200')),]
stopifnot(nrow(d)==32, !anyDuplicated(d[c('replication','model','condition')]))
models <- c('llama','qwen','gemma','mistral'); conditions<-c('baseline','exposure50','time200','memory4000')
d$cell <- (match(d$model,models)-1)*4+match(d$condition,conditions)
d$block <- as.integer(factor(paste(d$model,d$replication)))
write.csv(d,file.path(out,'count_model_input.csv'),row.names=FALSE)
s <- read.csv('replication_check/analysis/semantic_responses.csv')
s$cell <- (match(s$model,models)-1)*4 + (match(s$kind,c('meaning','application'))-1)*2 + match(s$state,c('initial','use'))
for(g in c('block','agentblock','word','item','case')) {
 v <- switch(g,block=paste(s$model,s$replication),agentblock=paste(s$model,s$replication,s$agent),word=s$term_id,item=s$item_id,case=paste(s$model,s$replication,s$case_id))
 s[[g]]<-as.integer(factor(v))
}
stopifnot(nrow(s)==1482,all(!is.na(s$cell)))
write.csv(s,file.path(out,'semantic_model_input.csv'),row.names=FALSE)
count_code <- '
data {int<lower=1> N; int<lower=1> C; int<lower=1> B; array[N] int<lower=0> y; array[N] int<lower=1,upper=C> cell; array[N] int<lower=1,upper=B> block; vector[N] log_messages; real<lower=0> beta_scale; real<lower=0> sd_scale; real<lower=0> shape_scale;}
parameters {vector[C] beta; vector[B] z_block; real<lower=0> sd_block; real log_shape;}
transformed parameters {vector[N] eta; real<lower=0> shape=exp(log_shape); for(n in 1:N) eta[n]=log_messages[n]+beta[cell[n]]+sd_block*z_block[block[n]];}
model {beta ~ normal(-2.5,beta_scale); z_block ~ std_normal(); sd_block ~ normal(0,sd_scale); log_shape ~ normal(log(10),shape_scale); y ~ neg_binomial_2_log(eta,shape);}
generated quantities {array[N] int y_rep; vector[N] log_lik; for(n in 1:N) {y_rep[n]=neg_binomial_2_log_rng(eta[n],shape); log_lik[n]=neg_binomial_2_log_lpmf(y[n]|eta[n],shape);}}
'
sem_code <- '
data {int<lower=1> N; int<lower=1> C; int<lower=1> B; int<lower=1> A; int<lower=1> W; int<lower=1> I; int<lower=1> K; array[N] int<lower=0,upper=1> y; array[N] int<lower=1,upper=C> cell; array[N] int<lower=1,upper=B> block; array[N] int<lower=1,upper=A> agent; array[N] int<lower=1,upper=W> word; array[N] int<lower=1,upper=I> item; array[N] int<lower=1,upper=K> case_id; real<lower=0> beta_scale; real<lower=0> sd_scale;}
parameters {vector[C] beta; vector[B] z_block; vector[A] z_agent; vector[W] z_word; vector[I] z_item; vector[K] z_case; vector<lower=0>[5] sd;}
transformed parameters {vector[N] eta; for(n in 1:N) eta[n]=beta[cell[n]]+sd[1]*z_block[block[n]]+sd[2]*z_agent[agent[n]]+sd[3]*z_word[word[n]]+sd[4]*z_item[item[n]]+sd[5]*z_case[case_id[n]];}
model {beta ~ normal(1.5,beta_scale); z_block ~ std_normal(); z_agent ~ std_normal(); z_word ~ std_normal(); z_item ~ std_normal(); z_case ~ std_normal(); sd ~ normal(0,sd_scale); y ~ bernoulli_logit(eta);}
generated quantities {array[N] int y_rep; vector[N] log_lik; for(n in 1:N) {y_rep[n]=bernoulli_logit_rng(eta[n]); log_lik[n]=bernoulli_logit_lpmf(y[n]|eta[n]);}}
'
writeLines(count_code,file.path(out,'count.stan'));invisible(NULL)
cd<-list(N=nrow(d),C=16,B=max(d$block),y=as.integer(d$occurrences),cell=d$cell,block=d$block,log_messages=log(d$messages),beta_scale=1.5,sd_scale=1,shape_scale=1.5)
sd<-list(N=nrow(s),C=16,B=max(s$block),A=max(s$agentblock),W=max(s$word),I=max(s$item),K=max(s$case),y=as.integer(s$correct),cell=s$cell,block=s$block,agent=s$agentblock,word=s$word,item=s$item,case_id=s$case,beta_scale=2,sd_scale=1)
for(type in c('count')) {
 mod<-cmdstan_model(file.path(out,paste0(type,'.stan')),cpp_options=list(stan_threads=FALSE))
 for(pr in c('primary','sensitivity')) {
  dat<-if(type=='count') cd else sd
  if(pr=='sensitivity'){ dat$beta_scale<-if(type=='count') 2.5 else 3; dat$sd_scale<-2; if(type=='count') dat$shape_scale<-2 }
  fit<-mod$sample(data=dat,seed=2026110700+match(type,c('count','semantic'))*10+match(pr,c('primary','sensitivity')),chains=4,parallel_chains=2,iter_warmup=1000,iter_sampling=4000,adapt_delta=.99,max_treedepth=13,refresh=500,output_dir=out,output_basename=paste(type,pr,sep='_'))
  fit$save_object(file.path(out,paste0(type,'_',pr,'.rds')))
  sm<-fit$summary(variables=if(type=='count') c('beta','sd_block','log_shape') else c('beta','sd'))
  write.csv(sm,file.path(out,paste0(type,'_',pr,'_parameters.csv')),row.names=FALSE)
  write.csv(fit$diagnostic_summary(),file.path(out,paste0(type,'_',pr,'_diagnostics.csv')),row.names=FALSE)
  draws<-as_draws_matrix(fit$draws(variables=c('beta','y_rep')))
  con<-list()
  for(m in seq_along(models)) {
   if(type=='count') {
    for(c in 2:4){v<-draws[,paste0('beta[',(m-1)*4+c,']')]-draws[,paste0('beta[',(m-1)*4+1,']')]; con[[length(con)+1]]<-data.frame(model=models[m],contrast=conditions[c],estimate=median(exp(v)),lower=quantile(exp(v),.025),upper=quantile(exp(v),.975),prob_increase=mean(v>0))}
   }else for(k in 1:2){v<-draws[,paste0('beta[',(m-1)*4+(k-1)*2+2,']')]-draws[,paste0('beta[',(m-1)*4+(k-1)*2+1,']')];con[[length(con)+1]]<-data.frame(model=models[m],contrast=c('meaning','application')[k],estimate=median(exp(v)),lower=quantile(exp(v),.025),upper=quantile(exp(v),.975),prob_increase=mean(v>0))}
  }
  write.csv(do.call(rbind,con),file.path(out,paste0(type,'_',pr,'_contrasts.csv')),row.names=FALSE)
  yr<-draws[,paste0('y_rep[',1:nrow(if(type=='count')d else s),']'),drop=FALSE]
  if(type=='count') {
   ppc<-data.frame(metric=c('total','maximum','variance','zero_rows'),observed=c(sum(d$occurrences),max(d$occurrences),var(d$occurrences),sum(d$occurrences==0)))
   zz<-cbind(rowSums(yr),apply(yr,1,max),apply(yr,1,var),rowSums(yr==0))
   ppc$predictive_median<-apply(zz,2,median);ppc$lower<-apply(zz,2,quantile,.025);ppc$upper<-apply(zz,2,quantile,.975);ppc$tail_probability<-sapply(1:4,function(j)mean(zz[,j]>=ppc$observed[j]))
  }else {
   ppc<-do.call(rbind,lapply(1:16,function(c){idx<-which(s$cell==c);v<-rowMeans(yr[,idx,drop=FALSE]);data.frame(cell=c,observed=mean(s$correct[idx]),predictive_median=median(v),lower=quantile(v,.025),upper=quantile(v,.975),tail_probability=mean(v>=mean(s$correct[idx])))}))
  }
  write.csv(ppc,file.path(out,paste0(type,'_',pr,'_ppc.csv')),row.names=FALSE)
  cat('\nCOMPLETED',type,pr,'\n'); flush.console()
 }
}
writeLines(capture.output(sessionInfo()),file.path(out,'sessionInfo.txt'))
