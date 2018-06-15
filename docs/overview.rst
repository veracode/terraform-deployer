Welcome to Veracode Terraform-Deployer

Welcome to the see-and-deploy Wiki, where you can (hopefully) find all the information you need about the projects.  The goal of Veracode terraform-deployer is to offer a generic gitlab-based project to bootstrap you and your team into AWS.  We offer a very basic Python-based deployer application which wraps around Terraform as the infrastructure orchestration piece, and allows you to add your applications, complete with their configuration management code, infrastructure code, and anything else necessary, as simple plugins to the deployer itself.

About us
We are just a few Veracoders (for now, we hope to expand the team!) who got frustrated with the disjointed way every project approached solving identical problems in different ways which were incompatible with each other. 

Together, we are attempting at making something which works across teams and projects in a generic manner such that all teams can (if they choose to) use the same tools and work-flows to solve their unique problems. This should allow teams to exchange members freely and get up to speed quickly with things like workflow, testing, upgrades, deployments, etc.

Architectural Discussions
- Deployer Architecture
- Terraform Architecture
- Individual Application Repository Layout
  - Application Source Code
  - Automated Build Environment
  - Configuration Management Code
  - Infrastructure & Deployment Configuration Code

HOW-TOs
- Deploy from your desktop
- Clean up after a failed pipeline
- Use the deployer in a pipeline
