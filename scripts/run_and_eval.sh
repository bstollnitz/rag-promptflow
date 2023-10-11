# create a name for the run
run_name=run_$(date +%Y%m%d_%H%M%S)
echo "run name: $run_name"
# create the run
pfazure run create -f promptflow/rag_job.yaml --name $run_name --stream
# evaluate the run
pfazure run create -f promptflow/eval_job.yaml --run $run_name --stream
