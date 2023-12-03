// MySQL 데이터베이스와 상호작용하기 위해 mysql 모듈을 가져옵니다.
const mysql = require("mysql");

// MySQL 연결 객체를 저장하기 위한 변수를 선언합니다.
let conn;

// createTable 함수 정의: 특정 데이터베이스에 테이블을 생성합니다.
function createTable(params) {
    // Promise를 반환합니다. 이를 통해 비동기적으로 테이블 생성 작업을 수행할 수 있습니다.
    return new Promise(function(resolve, reject) {
        // 연결 객체가 없는 경우, 새로운 연결을 생성합니다.
        if (!conn) {
            conn = mysql.createConnection({
                host: params.cdbHost,         // MySQL 호스트 주소
                user: params.cdbUser,         // MySQL 사용자 이름
                password: params.cdbPass,     // MySQL 비밀번호
                database: params.cdbDatabase  // 사용할 데이터베이스 이름
            });
            conn.connect(); // MySQL에 연결합니다.
        }

        // 테이블 생성 SQL 쿼리를 정의합니다.
        let query = `CREATE TABLE ${params.cdbTable}
                    (no INT NOT NULL AUTO_INCREMENT,
                    title VARCHAR(50),
                    author VARCHAR(30),
                    publisher VARCHAR(30),
                    PRIMARY KEY(no))`;

        // MySQL에 쿼리를 실행합니다.
        conn.query(query, function (error, results, fields) {
            if (error) {
                reject({ error: error }); // 오류가 발생한 경우 reject를 호출하여 오류를 처리합니다.
            }
            resolve(results); // 테이블 생성이 성공한 경우 resolve를 호출하여 결과를 반환합니다.
        });
    });
}

// createTable 함수를 모듈의 main 속성으로 내보냅니다.
exports.main = createTable;