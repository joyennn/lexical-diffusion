library(cmdstanr);library(posterior);library(jsonlite)
out<-normalizePath('output/LV_two_run_statistics/statistics');ans<-list()
for(type in c('count','semantic'))for(pr in c('primary','sensitivity')) {
 f<-readRDS(file.path(out,paste0(type,'_',pr,'.rds')))
 vars<-if(type=='count')c('beta','z_block','sd_block','log_shape')else c('beta','z_block','z_agent','z_word','z_item','z_case','z_block_slope','z_word_slope','sd')
 sm<-f$summary(variables=vars);di<-f$diagnostic_summary()
 write.csv(sm,file.path(out,paste0(type,'_',pr,'_all_parameters.csv')),row.names=FALSE)
 z<-list(fit=paste(type,pr),max_rhat=max(sm$rhat,na.rm=TRUE),min_ess_bulk=min(sm$ess_bulk,na.rm=TRUE),min_ess_tail=min(sm$ess_tail,na.rm=TRUE),divergences=sum(di$num_divergent),max_treedepth=sum(di$num_max_treedepth),min_ebfmi=min(di$ebfmi))
 ans[[length(ans)+1]]<-z
}
write_json(list(fits=ans),file.path(out,'model_diagnostics.json'),pretty=TRUE,auto_unbox=TRUE)
print(ans)
