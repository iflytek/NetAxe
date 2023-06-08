rabbitmqctl stop_app
rabbitmqctl reset
# rabbitmqctl join_cluster rabbitmq@rabbitmq1
rabbitmqctl start_app
#rabbitmqctl set_permissions -p /  admin ".*" ".*" ".*"
rabbitmqctl add_vhost netaxe
rabbitmqctl set_permissions -p netaxe adminnetaxe '.*' '.*' '.*'