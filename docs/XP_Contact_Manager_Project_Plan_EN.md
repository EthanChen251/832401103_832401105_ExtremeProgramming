# Extreme Programming Assignment — Project Plan

> **Working Project Name:** Contact Manager  
> **Course:** Software Engineering (FZU–MU)  
> **Assignment:** Extreme Programming (XP)  
> **Deadline:** November 17, 2026, 23:59  
> **Status:** Initial planning; detailed design has not started

## 1. Project Overview

This project aims to develop a web-based contact management system using a separated frontend and backend architecture. Users will be able to manage contacts, bookmark frequently used contacts, store multiple contact methods for one person, and import or export address-book data through Excel files.

The application will use a local SQLite database for persistent storage, so data remains available after normal application shutdown and restart. The priority is to meet the course requirements with a functional and stable implementation while practicing Git version control and collaborative software development associated with Extreme Programming.

## 2. Technology Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Frontend | Vue 3 | Build the user interface, components, and interactions |
| Frontend development and build | Vite | Provide a development server and build frontend assets |
| Backend | Python + Flask | Serve HTTP APIs, handle business logic and file operations |
| Database | SQLite | Persist contact information on the backend's local disk |
| Frontend–backend communication | HTTP + JSON | Exchange application data; Excel uses appropriate file upload/download handling |
| Version control and collaboration | Git + GitHub | Manage code, commits, releases, and pull requests |
| Excel processing | Python Excel library (to be selected) | Read and generate Excel files |

**Architecture summary:** The Vue frontend runs in a browser and communicates with the Flask backend over HTTP. The backend accesses SQLite; the frontend does not access the database directly.

## 3. Planned Features

### 3.1 Basic Contact Management

- Create contacts.
- View the contact list and contact details.
- Edit and delete existing contacts.
- Persist data locally and retrieve it after an application restart.

### 3.2 Bookmark Contacts (25 points)

- Mark and unmark contacts as favorites.
- Easily view bookmarked contacts.
- Persist favorite status.

### 3.3 Multiple Contact Methods (10 points)

- Store multiple contact methods for a single contact.
- Support categories such as phone numbers, email addresses, social media accounts, and physical addresses.
- Allow users to maintain existing contact methods.

### 3.4 Excel Import and Export (25 points)

- **Export:** Generate an Excel file containing contacts and their associated information, with one contact per row and separate columns for different information types, preserving multiple contact methods.
- **Import:** Read a correctly formatted Excel file and add its contacts to the address book.
- Display useful feedback for invalid files or data; verify that exported files can be imported correctly.

### 3.5 Page Style and Interaction (10 points)

- Provide a clean and usable web interface.
- Include basic form validation, operation feedback, and error messages.

### 3.6 Optional Features

- **Cloud deployment (+15 bonus points):** If time permits, deploy the complete web application to a publicly accessible cloud service, subject to the course's acceptance criteria.
- Search, sorting, and similar convenience features may be considered later, but are not committed requirements at this stage.

## 4. Development and Verification Principles

- Discuss module responsibilities, collaboration practices, and basic code standards before implementation.
- Use Git with incremental, traceable commits.
- Complete required features before optional enhancements or cloud deployment.
- Verify persistence across normal restarts and test bookmarking, multiple contact methods, and the full Excel import/export workflow.
- Record development difficulties, solutions, and individual effort for the blog and PSP tables.

## 5. High-Level Work Plan

| Phase | Activities |
| --- | --- |
| Preparation | Fork the assigned repository; confirm team responsibilities, development environment, and coding standards |
| Implementation | Build the frontend, Flask backend, SQLite persistence, and core features |
| Verification | Test functionality, persistence, and Excel round trips; record the software demonstration |
| Submission | Push code and documentation, create a Release and Pull Request, and publish and submit individual blogs |

## 6. Deliverables and Course Requirements

- Buildable, runnable source code with basic setup and run instructions.
- GitHub repository and coding-standard links; **at least 3 Git commits** as required by the assignment.
- A published Release and an initiated Pull Request.
- Screenshots and a complete video demonstration of the running application.
- **A separate Markdown blog submitted by each student**, including an assignment description, table of contents, project links, implementation ideas, Git history screenshots, commit counts by contributor, an individual PSP table, and a grading-rubric self-check. Team projects should also document task allocation, contribution percentages totaling 100%, and collaboration difficulties and resolutions.
- The required introductory information table in the blog (course, team name, assignment requirements, objectives, and other references).
- **Blogs require review after publication; publish early enough to avoid deadline issues.**

## 7. Scope and Open Decisions

**Current scope:** Basic management of one address book, bookmarks, multiple contact methods, Excel import/export, and local persistence. User accounts, multi-user synchronization, and advanced permission systems are not established requirements for this iteration.

**To be decided:** Assigned GitHub repository and existing code, team size and responsibilities, coding standards, Excel library, user interface design, and whether to attempt cloud deployment.

> This is a high-level project plan to align goals and scope. It intentionally does not define API endpoints, database tables, project directory structures, or other detailed technical design decisions. Those will be addressed separately during design and implementation.
