CREATE TABLE Tickets
(
TicketId int,
Ticket_Type varchar(255),
Customer varchar(255),
Current_Status varchar(255),
Time_Zone varchar(255),
Created_time DateTime,
Initiator varchar(255),
Category varchar(255),
Sub_Category varchar(255),
Service_Request_Classification varchar(255),
Monitored_Attribute varchar(255),
RFO varchar(255),
Priority int,
Vendor_Docket_number varchar(255),
Third_party_reference_number varchar(255),
Down_At DateTime,
Up_At DateTime,
CI_name varchar(255),
CI_IP varchar(255),
CI_Critical varchar(255),
CI_location varchar(255),
Title varchar(255),
Owner varchar(255),
Assigned_Group varchar(255),
Support_type varchar(255),
Requestor_name varchar(255),
Requestor_Reached_Helpdesk_by varchar(255),
Requestor_Email varchar(255),
Requestor_CC varchar(255),
Requestor_Phone_Mobile varchar(255),
Requestor_Location varchar(255),
Resolved_On DateTime,
Resolved_Time varchar(255),
Closed_Time DateTime,
Resolved_By varchar(255),
Closed_By varchar(255),
Branch_Name varchar(255),
Branch_Code varchar(255),
City_Name varchar(255),
State_Name varchar(255),
CI_Vendor_Name varchar(255),
Product_name varchar(255),
Incident_Vendor_Name varchar(255),
Service_Location varchar(255),
Reported_By varchar(255),
VIP_User int,
CCL varchar(255),

primary key(TicketId)
)


CREATE TABLE Descriptions
(
	TicketId int,
	TicketDescription text
);

CREATE TABLE Resolutions
(
	TicketId int,
	Resolution text,
	Resolved_On DateTime
);

CREATE TABLE Ccls
(
	TicketId int,
	ccl varchar(255)
)

CREATE TABLE Comments
(
	TicketId int,
	Satisfaction varchar(255),
	Comment text
);

CREATE TABLE Users
(
	username varchar(255)
)

CREATE TABLE Issues
(
	issue varchar(255)
)

CREATE VIEW GBSTickets as
(
	SELECT *
	FROM Tickets
	WHERE Requestor_name in (SELECT * FROM Users) or Owner in (SELECT * FROM Users) or Assigned_Group = 'FordGBS'
)

CREATE VIEW GBSReport as
(
	SELECT T.TicketId, T.Ticket_Type, C.Ccl, D.TicketDescription, T.Service_Request_Classification as Issue_Type, T.Owner, T.Priority, T.Current_Status, T.Requestor_name, T.Resolved_Time, T.Created_time, T.Resolved_On, T.Closed_Time, R.Resolution, Co.Satisfaction, Co.Comment
	FROM GBSTickets T
		LEFT OUTER JOIN Ccls C on T.TicketId = C.TicketId
		LEFT OUTER JOIN Descriptions D on T.TicketId = D.TicketId
		LEFT OUTER JOIN Resolutions R on T.TicketId = R.TicketId
		LEFT OUTER JOIN Comments Co on T.TicketId = Co.TicketId
)

CREATE VIEW GeorgeReport as
(
	SELECT *
	FROM GBSReport G
	WHERE G.Issue_Type not in (SELECT * FROM Issues) and G.Requestor_name in (SELECT * FROM Users)
)

CREATE VIEW KevinReport as
(
	SELECT T.TicketId, C.Ccl as CCL_Number, C.Status as CCL_Status, D.TicketDescription, T.Service_Request_Classification as Issue_Type, T.Owner, T.Priority, T.Current_Status as mWatch_Status, T.Requestor_name, T.Resolved_Time, T.Created_time, T.Resolved_On, T.Closed_Time, R.Resolution
	FROM GBSTickets T
		LEFT OUTER JOIN Ccls C on T.TicketId = C.TicketId
		LEFT OUTER JOIN Descriptions D on T.TicketId = D.TicketId
		LEFT OUTER JOIN Resolutions R on T.TicketId = R.TicketId
		LEFT OUTER JOIN Comments Co on T.TicketId = Co.TicketId
)

INSERT INTO Users VALUES ('Agrawal, Mitali')
INSERT INTO Users VALUES ('Ashok')
INSERT INTO Users VALUES ('Ashok Kumar')
INSERT INTO Users VALUES ('Ashok Kumar Nagelli')
INSERT INTO Users VALUES ('Bet Mendoza')
INSERT INTO Users VALUES ('Bharathipura Laxmanrao , Priyadarshi')
INSERT INTO Users VALUES ('Fertig, George')
INSERT INTO Users VALUES ('GALAXEDEV1 Support')
INSERT INTO Users VALUES ('Galaxedev2')
INSERT INTO Users VALUES ('GBS Dev')
INSERT INTO Users VALUES ('GBSIIQA_BuildAdmin')
INSERT INTO Users VALUES ('George Fertig')
INSERT INTO Users VALUES ('Henry Kwok')
INSERT INTO Users VALUES ('Hillier, Scot')
INSERT INTO Users VALUES ('jayanthi')
INSERT INTO Users VALUES ('jitendra')
INSERT INTO Users VALUES ('Jitendra kumar')
INSERT INTO Users VALUES ('Jitendra Rawat')
INSERT INTO Users VALUES ('Jose, Lijo')
INSERT INTO Users VALUES ('K.Zhao')
INSERT INTO Users VALUES ('Kasara, Kamesh')
INSERT INTO Users VALUES ('Kavitha Kothur')
INSERT INTO Users VALUES ('Kevin Zhao')
INSERT INTO Users VALUES ('Kim Kwangcheol')
INSERT INTO Users VALUES ('Kim, Kwangcheol')
INSERT INTO Users VALUES ('Kothur, Kavitha')
INSERT INTO Users VALUES ('kumar,ashok')
INSERT INTO Users VALUES ('Kwangcheol Kim')
INSERT INTO Users VALUES ('Kwok, Henry')
INSERT INTO Users VALUES ('L.Ponce')
INSERT INTO Users VALUES ('Lijo jose')
INSERT INTO Users VALUES ('Lucius Ponce')
INSERT INTO Users VALUES ('Mendoza, Bet')
INSERT INTO Users VALUES ('Mitali Agrawal')
INSERT INTO Users VALUES ('Nagelli, Ashok Kumar')
INSERT INTO Users VALUES ('Nanjappa, Chandrashekar Basavahalli')
INSERT INTO Users VALUES ('Oliver Triunfo')
INSERT INTO Users VALUES ('Ponce, Lucius')
INSERT INTO Users VALUES ('Priyadarshi')
INSERT INTO Users VALUES ('Priyadarshi Bharathipura Laxmanrao')
INSERT INTO Users VALUES ('Qinghua Sun')
INSERT INTO Users VALUES ('Sathish Kumar')
INSERT INTO Users VALUES ('sathishkumar')
INSERT INTO Users VALUES ('Sathishkumar  Rangasamy')
INSERT INTO Users VALUES ('Sathishkumar Rangasamy')
INSERT INTO Users VALUES ('Sathishkumar Rangaswamy')
INSERT INTO Users VALUES ('Sun, Qinghua')
INSERT INTO Users VALUES ('Triunfo, Oliver')
INSERT INTO Users VALUES ('Zhao, Kevin')
INSERT INTO Users VALUES ('Zhao, Shuyuan')

INSERT INTO Issues VALUES('CMS Outlook Client Installation / Configuration')
INSERT INTO Issues VALUES('CMS Web Client Installation / Configuration')
INSERT INTO Issues VALUES('CRM CMS Issue')
INSERT INTO Issues VALUES('CRM- Installation/Configuration')
INSERT INTO Issues VALUES('CRM- Issue')
INSERT INTO Issues VALUES('Document generator For FordGBS- Installation / Configuration')
INSERT INTO Issues VALUES('Document generator For FordGBS- Issue')
INSERT INTO Issues VALUES('Easy Upload for FordGBS- Installation / Configuration')
INSERT INTO Issues VALUES('Easy Upload for FordGBS- Issue')
INSERT INTO Issues VALUES('eTime (ADP)- Issue')
INSERT INTO Issues VALUES('eTime (ADP)- Password Reset')
INSERT INTO Issues VALUES('Ford GBS (Grants and Budgeting System)-issue')
INSERT INTO Issues VALUES('FordGBS - Access to application')
INSERT INTO Issues VALUES('FordGBS - Budget')
INSERT INTO Issues VALUES('FordGBS - CGen (Reminder Letters)')
INSERT INTO Issues VALUES('FordGBS - DocGen (RGA, GNL, etc.) Issue')
INSERT INTO Issues VALUES('FordGBS - EasyUpload/VGL Issue')
INSERT INTO Issues VALUES('FordGBS - Emails')
INSERT INTO Issues VALUES('FordGBS - Grantee Reporting')
INSERT INTO Issues VALUES('FordGBS - History incorrect/missing')
INSERT INTO Issues VALUES('FordGBS - Internal Dev Task')
INSERT INTO Issues VALUES('FordGBS - Lists and Filters')
INSERT INTO Issues VALUES('FordGBS - Other')
INSERT INTO Issues VALUES('FordGBS - Payments')
INSERT INTO Issues VALUES('FordGBS - Report Builder/DW')
INSERT INTO Issues VALUES('FordGBS - Request Processing')
INSERT INTO Issues VALUES('FordGBS - System Errors')
INSERT INTO Issues VALUES('FordGBS - TDL')
INSERT INTO Issues VALUES('FordGBS - User Interface')
INSERT INTO Issues VALUES('FordGBS (Grant and Budgets System)- Data Quick-Fix')
INSERT INTO Issues VALUES('FordGBS (Grant and Budgets System)- Migration and Release')
INSERT INTO Issues VALUES('FordGBS (Grant and Budgets System)- Reports & Dashboards')
INSERT INTO Issues VALUES('FordGBS (Grant and Budgets System)- Systems & Integration')
INSERT INTO Issues VALUES('FordGBS (Grant and Budgets System)- User Interface')
INSERT INTO Issues VALUES('FordGBS (Grant and Budgets System)- Workflow')
INSERT INTO Issues VALUES('FordGBS (Grantee Budgesting System) Error')
INSERT INTO Issues VALUES('FordNet- Issue')
INSERT INTO Issues VALUES('Forecaster- Installation / Configuration')
INSERT INTO Issues VALUES('Grantee Access- Issue')
INSERT INTO Issues VALUES('Grantee Portal Access')
INSERT INTO Issues VALUES('Microsoft GP (Dynamics)- Issue')
INSERT INTO Issues VALUES('Workplace- Issue')
INSERT INTO Issues VALUES('--Requests--')
INSERT INTO Issues VALUES('CMS Outlook Client Installation / Configuration')
INSERT INTO Issues VALUES('CRM- Installation/Configuration')
INSERT INTO Issues VALUES('Document generator For FordGBS- Installation / Configuration')
INSERT INTO Issues VALUES('Easy Upload for FordGBS- Installation / Configuration')
INSERT INTO Issues VALUES('eTime (ADP)- Password Reset')
INSERT INTO Issues VALUES('FordGBS (Grant and Budgets System)- Communications & Reporting')
INSERT INTO Issues VALUES('FordGBS (Grant and Budgets System)- Reports & Dashboards')
INSERT INTO Issues VALUES('FordGBS (Grant and Budgets System)- Workflow')
INSERT INTO Issues VALUES('FordNet- Enhancement Request')
INSERT INTO Issues VALUES('Microsoft GP (Dynamics)- Account Creation')
INSERT INTO Issues VALUES('Workplace- Installation / Configuration')