
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    review_text TEXT NOT NULL,
    embedding VECTOR(384)
);

INSERT INTO reviews (review_text)
VALUES
('I absolutely loved this movie. The acting was amazing.'),
('This was the worst movie I have ever watched.'),
('The story was interesting but the ending was disappointing.'),
('I would definitely recommend this movie to my friends.'),
('The movie was boring and I almost fell asleep.');
