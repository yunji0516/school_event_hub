-- 데이터베이스 생성 및 사용
CREATE DATABASE IF NOT EXISTS eventmanagement;
USE eventmanagement;

-- 테이블 생성
CREATE TABLE `user` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin', 'superadmin') NOT NULL DEFAULT 'user'
);

CREATE TABLE `location` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE `event` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    location_id INT,
    description TEXT,
    user_id INT NOT NULL,
    CONSTRAINT fk_event_location FOREIGN KEY (location_id) REFERENCES `location`(id) ON DELETE SET NULL,
    CONSTRAINT fk_event_user FOREIGN KEY (user_id) REFERENCES `user`(id) ON DELETE CASCADE,
    CONSTRAINT check_title_not_empty CHECK (title <> '')
);

CREATE TABLE `participant` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    contact VARCHAR(15) NOT NULL,
    student_id VARCHAR(15) NOT NULL,
    event_id INT NOT NULL,
    user_id INT NOT NULL,
    attendance BOOLEAN DEFAULT TRUE,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    CONSTRAINT fk_participant_event FOREIGN KEY (event_id) REFERENCES `event`(id) ON DELETE CASCADE,
    CONSTRAINT fk_participant_user FOREIGN KEY (user_id) REFERENCES `user`(id) ON DELETE CASCADE,
    CONSTRAINT unique_event_contact UNIQUE (event_id, contact),
    CONSTRAINT unique_event_student_id UNIQUE (event_id, student_id)
);

CREATE TABLE `feedback` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    feedback_text TEXT NOT NULL,
    rating INT NOT NULL,
    CONSTRAINT fk_feedback_event FOREIGN KEY (event_id) REFERENCES `event`(id) ON DELETE CASCADE,
    CONSTRAINT check_feedback_not_empty CHECK (feedback_text <> ''),
    CONSTRAINT check_rating_range CHECK (rating >= 1 AND rating <= 5)
);

-- 인덱스 생성
CREATE INDEX idx_user_email ON `user` (email);

CREATE INDEX idx_event_title ON `event` (title);
CREATE INDEX idx_event_date ON `event` (date);
CREATE INDEX idx_event_user_id ON `event` (user_id);

CREATE INDEX idx_participant_event_id ON `participant` (event_id);
CREATE INDEX idx_participant_user_id ON `participant` (user_id);

CREATE INDEX idx_feedback_event_id ON `feedback` (event_id);

-- 뷰 생성
CREATE VIEW EventAttendance AS
SELECT
    e.id AS event_id,
    e.title AS event_title,
    COUNT(p.id) AS total_participants,
    SUM(CASE WHEN p.attendance = TRUE THEN 1 ELSE 0 END) AS total_attendees,
    IFNULL(AVG(f.rating), 0) AS average_rating
FROM
    `event` e
LEFT JOIN `participant` p ON e.id = p.event_id
LEFT JOIN `feedback` f ON e.id = f.event_id
GROUP BY
    e.id;

-- 트리거 생성
DELIMITER $$

-- 이벤트 생성 시 과거 날짜 방지
CREATE TRIGGER trg_prevent_past_event_date_insert
BEFORE INSERT ON `event`
FOR EACH ROW
BEGIN
    IF NEW.date < CURRENT_DATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '이벤트 날짜는 과거일 수 없습니다.';
    END IF;
END $$

-- 이벤트 업데이트 시 과거 날짜 방지
CREATE TRIGGER trg_prevent_past_event_date_update
BEFORE UPDATE ON `event`
FOR EACH ROW
BEGIN
    IF NEW.date < CURRENT_DATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '이벤트 날짜는 과거일 수 없습니다.';
    END IF;
END $$

-- 참가자 연락처 검증 트리거 (삽입 시)
CREATE TRIGGER trg_validate_participant_contact
BEFORE INSERT ON `participant`
FOR EACH ROW
BEGIN
    IF NEW.contact NOT REGEXP '^[+]?[0-9]{10,15}$' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '유효하지 않은 연락처 형식입니다.';
    END IF;
END $$

-- 참가자 연락처 검증 트리거 (업데이트 시)
CREATE TRIGGER trg_validate_participant_contact_update
BEFORE UPDATE ON `participant`
FOR EACH ROW
BEGIN
    IF NEW.contact NOT REGEXP '^[+]?[0-9]{10,15}$' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '유효하지 않은 연락처 형식입니다.';
    END IF;
END $$

DELIMITER ;

-- 뷰 생성
-- 이벤트별 참가자 수 뷰
CREATE OR REPLACE VIEW event_participant_counts AS
SELECT
    e.id AS event_id,
    e.title AS event_title,
    COUNT(p.id) AS participant_count
FROM
    `event` e
LEFT JOIN
    `participant` p ON e.id = p.event_id
GROUP BY
    e.id;

-- 인기 있는 이벤트 뷰
CREATE OR REPLACE VIEW popular_events AS
SELECT
    e.id,
    e.title,
    e.date,
    COUNT(p.id) AS participant_count
FROM
    `event` e
LEFT JOIN
    `participant` p ON e.id = p.event_id
GROUP BY
    e.id
ORDER BY
    participant_count DESC;

-- 참가자 상세 정보 뷰
CREATE OR REPLACE VIEW participant_details AS
SELECT
    p.id AS participant_id,
    p.name AS participant_name,
    p.contact AS participant_contact,
    p.attendance,
    p.uuid,
    e.id AS event_id,
    e.title AS event_title,
    e.date AS event_date,
    u.id AS user_id,
    u.name AS user_name
FROM
    `participant` p
JOIN
    `event` e ON p.event_id = e.id
JOIN
    `user` u ON p.user_id = u.id;

-- 이벤트 참석률 뷰
CREATE OR REPLACE VIEW event_attendance_rates AS
SELECT
    e.id AS event_id,
    e.title AS event_title,
    (SUM(CASE WHEN p.attendance THEN 1 ELSE 0 END) / COUNT(p.id)) * 100 AS attendance_rate
FROM
    `event` e
JOIN
    `participant` p ON e.id = p.event_id
GROUP BY
    e.id;

-- 이벤트 제목과 설명에 대한 전체 텍스트 검색 인덱스 생성
ALTER TABLE `event` ADD FULLTEXT INDEX idx_event_full_text_search (title, description);

-- 참가자의 이름과 연락처에 대한 인덱스 생성
CREATE INDEX idx_participant_name_contact ON `participant` (name, contact);

-- 더미 데이터 삽입
INSERT INTO `user` (id, name, email, password, role)
VALUES
(1, '김윤지', 'admin@example.com', '$2b$12$e0NR4CF0YvSxewgqGH6r0uXIOhV3dKllAyMKpjpCK3nRRQmNPOad6', 'superadmin');

INSERT INTO `user` (name, email, password, role) VALUES
('홍길동', 'user1@example.com', '$2b$12$abcdefghijk1234567890uvwxyzABCD', 'user'),
('이영희', 'user2@example.com', '$2b$12$lmnopqrstuv9876543210wxyzEFGH', 'user'),
('박철수', 'admin2@example.com', '$2b$12$12345ABCDEfghijklmnopqrsUVWXYZ', 'admin');

INSERT INTO `location` (name) VALUES
('서울'),
('부산'),
('대구'),
('인천');

INSERT INTO `event` (title, date, location_id, description, user_id) VALUES
('서울 개발자 컨퍼런스', '2024-12-15', 1, '최신 기술 동향 공유 및 네트워킹 행사입니다.', 1),
('부산 스타트업 미팅', '2025-01-20', 2, '스타트업 기업들의 교류를 위한 자리입니다.', 4),
('대구 AI 워크숍', '2025-02-10', 3, '인공지능 기술에 대한 워크숍입니다.', 1);

-- 수정된 participant 데이터 삽입
INSERT INTO `participant` (name, contact, student_id, event_id, user_id, attendance, uuid) VALUES
('김철민', '01012345678', '2018123456', 1, 2, TRUE, UUID()),
('이수진', '01087654321', '2019123456', 1, 2, FALSE, UUID()),
('박영수', '01011112222', '2017123456', 2, 3, TRUE, UUID()),
('최은희', '01033334444', '2020123456', 3, 2, TRUE, UUID());

SELECT * FROM `event`;

INSERT INTO `feedback` (event_id, feedback_text, rating) VALUES
(1, '매우 유익한 시간이었습니다.', 5),
(2, '좋은 네트워킹 기회였습니다.', 4),
(3, 'AI에 대해 많이 배웠습니다.', 5);