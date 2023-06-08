create user netaxe@localhost identified by 'netaxe_pwd';
grant all on *.* to netaxe@'%' identified by 'netaxe_pwd';
grant all on *.* to netaxe@localhost identified by 'netaxe_pwd';
grant all on *.* to netaxe@'%' identified by 'netaxe_pwd' with grant option;
grant all privileges on *.* to root@'%' identified by 'root_devnet@2022';
flush privileges;
