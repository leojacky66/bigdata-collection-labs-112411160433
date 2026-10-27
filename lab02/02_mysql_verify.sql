-- 实验二第三阶段：只读核对，不修改数据。
USE smartpark_lab;

SELECT COUNT(*) AS after_count FROM houseinfo;

SELECT title, house, address, `struct`, area, floor, maketime, price
FROM houseinfo ORDER BY id LIMIT 5;

-- 对八个房源字段分组，核对唯一记录数。
SELECT COUNT(*) AS unique_record_count
FROM (
    SELECT title, house, address, `struct`, area, floor, maketime, price
    FROM houseinfo
    GROUP BY title, house, address, `struct`, area, floor, maketime, price
) AS unique_records;
