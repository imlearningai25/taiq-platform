-- Initial seed data for TaIQ platform
-- Industries
INSERT INTO industries (name, slug, icon) VALUES
('Technology', 'technology', '💻'),
('Healthcare', 'healthcare', '🏥'),
('Finance', 'finance', '💰'),
('Engineering', 'engineering', '⚙️'),
('Marketing', 'marketing', '📣'),
('Education', 'education', '🎓'),
('Manufacturing', 'manufacturing', '🏭'),
('Retail', 'retail', '🛍️'),
('Logistics', 'logistics', '🚚'),
('Legal', 'legal', '⚖️')
ON CONFLICT DO NOTHING;

-- Sample testimonials
INSERT INTO testimonials (name, role, company, content, rating) VALUES
('Sarah Johnson', 'Software Engineer', 'Google', 'TaIQ connected me with my dream job in just 2 weeks. The platform is intuitive and the team is incredibly supportive throughout the process.', 5),
('Michael Chen', 'HR Director', 'Pfizer', 'We have been using TaIQ to source top-tier candidates and the quality of applicants is consistently excellent. Highly recommended for any growing company.', 5),
('Priya Patel', 'Data Scientist', 'Goldman Sachs', 'After months of searching on other platforms, TaIQ matched me with the perfect role that aligned with both my skills and career goals.', 5),
('James Williams', 'Operations Manager', 'Amazon', 'The talent pool on TaIQ is exceptional. We filled 12 positions in a single quarter, saving us significant time and recruiting costs.', 4),
('Emma Rodriguez', 'UX Designer', 'Apple', 'Simple, clean, and effective. I uploaded my resume, filled in my preferences, and had 5 interview invitations within a week.', 5),
('David Kim', 'CFO', 'Tesla', 'TaIQ has become our primary recruiting channel. The quality of candidates and the platform support are unmatched in the industry.', 5)
ON CONFLICT DO NOTHING;
