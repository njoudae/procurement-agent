USE ProcurementAgent;
GO

INSERT INTO dbo.Vendors (CompanyName, Category, Department, Email, Phone, Rating, IsActive)
VALUES
('Nexus IT Supply', 'IT Hardware', 'IT', 'jo11sa610@gmail.com', '+966582968140', 4.8, 1),
('BrightOffice Solutions', 'Office Supplies', 'Operations', 'jo11sa610@gmail.com', '+966582968140', 4.4, 1),
('MedEquip Partners', 'Medical Equipment', 'Clinical', 'jo11sa610@gmail.com', '+966582968140', 4.7, 1),
('Facilities Pro Services', 'Facilities', 'Operations', 'jo11sa610@gmail.com', '+966582968140', 4.2, 1),
('CloudWorks Licensing', 'Software', 'IT', 'jo11sa610@gmail.com', '+966582968140', 4.6, 1),
('Legacy Inactive Vendor', 'IT Hardware', 'IT', 'jo11sa610@gmail.com', '+966582968140', 5.0, 0);
GO

INSERT INTO dbo.PurchaseRequests (RequesterName, Department, ItemDescription, Category, Quantity, Budget, Urgency, RequiredDate, OriginalText, Status)
VALUES (
    'Sarah Ahmed',
    'IT',
    'Business laptops for onboarding',
    'IT Hardware',
    12,
    18000.00,
    'medium',
    DATEADD(day, 30, CAST(GETUTCDATE() AS date)),
    'Sarah from IT needs 12 business laptops for onboarding next month. Budget is around 18000 USD. Please request quotes from approved IT hardware vendors.',
    'New'
);
GO
