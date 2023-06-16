CREATE DATABASE IF NOT EXISTS netaxe
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

CREATE DATABASE IF NOT EXISTS rbac
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

CREATE DATABASE IF NOT EXISTS msggateway
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

CREATE DATABASE IF NOT EXISTS ipam
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

CREATE DATABASE IF NOT EXISTS alertgateway
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

CREATE DATABASE IF NOT EXISTS neteye
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

create user netaxe@localhost identified by 'netaxe_pwd';
grant all on *.* to netaxe@'%' identified by 'netaxe_pwd';
grant all on *.* to netaxe@localhost identified by 'netaxe_pwd';
grant all on *.* to netaxe@'%' identified by 'netaxe_pwd' with grant option;
grant all privileges on *.* to root@'%' identified by 'root_devnet@2022';
flush privileges;
