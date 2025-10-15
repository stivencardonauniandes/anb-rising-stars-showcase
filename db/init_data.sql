-- Active: 1750946230291@@127.0.0.1@5432@anb_showcase
-- Insert test data for users table
INSERT INTO users (id, email, first_name, last_name, password, city, country) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'john.doe@example.com', 'John', 'Doe', 'hashedpassword1', 'New York', 'USA'),
('550e8400-e29b-41d4-a716-446655440001', 'jane.smith@example.com', 'Jane', 'Smith', 'hashedpassword2', 'London', 'UK'),
('550e8400-e29b-41d4-a716-446655440002', 'alice.johnson@example.com', 'Alice', 'Johnson', 'hashedpassword3', 'Paris', 'France');

-- Insert test data for videos table
INSERT INTO videos (id, user_id, raw_video_id, processed_video_id, title, status, uploaded_at, processed_at, original_url, processed_url, votes) VALUES
('550e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440005', 'My First Video', 'processed', '2023-10-01 10:00:00+00', '2023-10-01 10:30:00+00', 'https://example.com/raw1.mp4', 'https://example.com/processed1.mp4', 5),
('550e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440007', NULL, 'Vacation Highlights', 'uploaded', '2023-10-02 11:00:00+00', NULL, 'https://example.com/raw2.mp4', NULL, 2),
('550e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440010', 'Cooking Tutorial', 'processed', '2023-10-03 12:00:00+00', '2023-10-03 12:45:00+00', 'https://example.com/raw3.mp4', 'https://example.com/processed3.mp4', 8);

-- Insert test data for votes table
INSERT INTO votes (user_id, video_id) VALUES
('550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440003'),
('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440003'),
('550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440003'),
('550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440006'),
('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440006'),
('550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440008'),
('550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440008'),
('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440008');