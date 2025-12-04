# Data Model: Physical AI & Humanoid Robotics Educational Platform

## Core Entities

### Module
**Purpose**: Represents major educational modules in the robotics curriculum

**Fields**:
- `id`: string - Unique identifier (e.g., "module-1-nervous-system")
- `number`: integer - Module number (1-4)
- `title`: string - Module title (display name)
- `description`: string - Module overview and objectives
- `duration_weeks`: integer - Duration in weeks
- `chapters`: array<string> - List of chapter IDs in this module
- `hardware_requirements`: array<HardwareRequirement> - Required hardware for this module
- `learning_outcomes`: array<string> - Module-level learning outcomes
- `prerequisites`: array<string> - Required prior knowledge or modules

**Validation Rules**:
- `number` must be between 1-4
- `chapters` must be sequential within module
- `hardware_requirements` must include cloud alternatives

### Chapter
**Purpose**: Represents individual educational chapters within modules

**Fields**:
- `id`: string - Unique identifier (e.g., "chapter-1-introduction")
- `title`: string - Chapter title (display name)
- `description`: string - Chapter description for SEO and navigation
- `slug`: string - URL slug for web navigation
- `module_id`: string - Reference to parent module
- `chapter_number`: integer - Chapter number within module
- `week_number`: integer - Week in 13-week curriculum
- `estimated_time`: integer - Estimated reading time in minutes
- `difficulty`: enum - "beginner" | "intermediate" | "advanced"
- `hardware_tiers`: array<HardwareTier> - Supported hardware configurations
- `cloud_alternative`: boolean - Cloud deployment option available
- `prerequisites`: array<string> - List of prerequisite chapter IDs
- `tags`: array<string> - Content tags for categorization
- `authors`: array<string> - Chapter authors/contributors
- `last_updated`: datetime - Last modification timestamp

**Validation Rules**:
- `id` must be unique across all chapters
- `slug` must be URL-safe and unique
- `module_id` must reference valid module
- `week_number` must be between 1-13

### HardwareRequirement
**Purpose**: Specifies hardware requirements for educational content

**Fields**:
- `id`: string - Unique identifier
- `component_type`: enum - "workstation" | "gpu" | "cpu" | "ram" | "storage" | "robot" | "sensor"
- `minimum_specification`: string - Minimum required specification
- `recommended_specification`: string - Recommended specification
- `cost_estimate`: object - Cost estimation object
  - `individual`: number - Cost for individual student
  - `institutional`: number - Cost for institution setup
  - `currency`: string - Currency code (USD, EUR, etc.)
- `alternatives`: array<string> - Alternative solutions or cloud options
- `justification`: string - Why this hardware is required

### HardwareTier
**Purpose**: Defines hardware configuration tiers for accessibility

**Fields**:
- `tier`: enum - "basic" | "intermediate" | "advanced" | "premium"
- `name`: string - Display name (e.g., "Edge Kit Only", "Workstation Setup", "Cloud Native")
- `description`: string - Tier description and use case
- `components`: array<HardwareComponent> - Required hardware components
- `total_cost`: number - Estimated total cost
- `setup_difficulty`: enum - "easy" | "moderate" | "complex"
- `limitations`: array<string> - Known limitations or constraints

### LearningObjective
**Purpose**: Defines specific learning outcomes for chapters and modules

**Fields**:
- `id`: string - Unique identifier
- `chapter_id`: string - Reference to parent chapter (nullable for module-level)
- `module_id`: string - Reference to parent module
- `objective`: string - Learning objective description
- `type`: enum - "knowledge" | "skill" | "application" | "analysis" | "evaluation" | "creation"
- `blooms_level`: integer - Bloom's Taxonomy level (1-6)
- `hardware_dependency`: boolean - Requires specific hardware to demonstrate
- `assessment_method`: string - How objective will be assessed
- `industry_relevance`: string - Connection to industry requirements

### CodeExample
**Purpose**: Represents executable code examples within chapters

**Fields**:
- `id`: string - Unique identifier
- `chapter_id`: string - Reference to parent chapter
- `title`: string - Example title/description
- `language`: enum - "python" | "cpp" | "yaml" | "xml" | "bash" | "unity"
- `purpose`: string - What this code demonstrates
- `complexity`: enum - "basic" | "intermediate" | "advanced"
- `hardware_tiers`: array<HardwareTier> - Supported hardware configurations
- `cloud_compatible`: boolean - Can run in cloud environment
- `dependencies`: array<string> - Required packages/libraries
- `expected_output`: string - Expected result/output
- `file_path`: string - Path to code file in repo
- `execution_time`: integer - Estimated execution time in seconds
- `memory_requirements`: string - RAM requirements for execution

**Validation Rules**:
- `file_path` must exist in repository
- `dependencies` must be compatible with LTS versions
- At least one `hardware_tiers` must be specified

### BudgetPlan
**Purpose**: Manages budget planning for different scenarios

**Fields**:
- `id`: string - Unique identifier
- `scenario`: enum - "individual_student" | "institution_lab" | "research_group"
- `hardware_tier`: HardwareTier reference
- `components`: array<BudgetItem> - Individual budget items
- `total_cost`: number - Total estimated cost
- `funding_sources`: array<string> - Potential funding sources
- `roi_timeline`: integer - Return on investment timeline in months
- **maintenance_cost**: number - Annual maintenance cost

### BudgetItem
**Purpose**: Individual budget items for planning

**Fields**:
- `id`: string - Unique identifier
- `category`: enum - "hardware" | "software" | "cloud" | "maintenance" | "training"
- `item_name`: string - Specific item name
- `quantity`: integer - Quantity required
- `unit_cost`: number - Cost per unit
- `total_cost`: number - Total cost (quantity × unit_cost)
- `vendor`: string - Recommended vendor or supplier
- `alternatives`: array<string> - Alternative options with cost differences

### CloudAlternative
**Purpose**: Cloud-based alternatives to hardware requirements

**Fields**:
- `id`: string - Unique identifier
- `hardware_component`: HardwareComponent reference
- `cloud_provider`: string - Cloud service provider (AWS, GCP, Azure)
- `service_name`: string - Specific cloud service (e.g., "g5.2xlarge")
- `hourly_cost`: number - Cost per hour
- `estimated_monthly_cost`: number - Estimated monthly usage cost
- `setup_complexity`: enum - "easy" | "moderate" | "complex"
- **limitations**: array<string> - Cloud-specific limitations
- `advantages`: array<string> - Benefits over local hardware

### CapstoneProject
**Purpose**: Manages capstone project integration and requirements

**Fields**:
- `id`: string - Unique identifier
- `title`: string - Project title
- `description`: string - Project overview and objectives
- `required_modules`: array<string> - Required module completions
- `hardware_requirements`: array<HardwareRequirement> - Project-specific hardware
- `estimated_duration`: integer - Duration in hours
- `difficulty`: enum - "intermediate" | "advanced"
- **team_size**: object - Min/max team size
  - `minimum`: integer
  - `maximum`: integer
- `deliverables`: array<string> - Expected project deliverables
- `assessment_criteria`: array<string> - Grading criteria

### Assessment
**Purpose**: Represents knowledge checks and evaluations

**Fields**:
- `id`: string - Unique identifier
- `chapter_id`: string - Reference to parent chapter
- `title`: string - Assessment title
- `type`: enum - "knowledge_check" | "coding_exercise" | "simulation_task" | "hardware_setup"
- `question`: string - Question text or task description
- `hardware_required`: boolean - Requires specific hardware
- `cloud_available`: boolean - Available in cloud environment
- `difficulty`: enum - "easy" | "medium" | "hard"
- `estimated_time`: integer - Time to complete in minutes
- **scoring**: object - Scoring rubric
  - `max_points`: integer
  - `passing_threshold`: number
  - `grading_criteria`: array<string>

## Content Structure Entities

### LabInfrastructure
**Purpose**: Manages lab setup and configuration guides

**Fields**:
- `id`: string - Unique identifier
- `setup_type`: enum - "workstation" | "cloud" | "jetson" | "robot"
- `title`: string - Setup guide title
- `prerequisites`: array<string> - Required prior setup
- `steps`: array<SetupStep> - Sequential setup steps
- `validation_commands`: array<string> - Commands to validate setup
- `troubleshooting_guide`: array<TroubleshootingItem> - Common issues and solutions
- **estimated_time**: integer - Total setup time in minutes

### SetupStep
**Purpose**: Individual steps in lab setup processes

**Fields**:
- `step_number`: integer - Sequential step number
- `title`: string - Step title
- `description`: string - Detailed instructions
- `commands`: array<string> - Commands to execute
- `expected_output`: string - Expected result
- **validation_check**: string - How to verify step completion
- `time_estimate`: integer - Estimated time in minutes

## Educational Progress Entities

### StudentProgress
**Purpose**: Tracks individual student progress through curriculum

**Fields**:
- `student_id`: string - Student identifier
- `module_id`: string - Module identifier
- `chapter_id`: string - Chapter identifier (nullable for module-level)
- `completed`: boolean - Completion status
- `completion_date`: datetime - When completed
- `time_spent`: integer - Time spent in minutes
- `assessment_scores`: array<AssessmentScore> - Assessment results
- `hardware_config`: HardwareTier reference - Used hardware configuration
- `notes`: text - Student notes or feedback

### HardwareConfiguration
**Purpose**: Tracks student's hardware setup and capabilities

**Fields**:
- `student_id`: string - Student identifier
- `hardware_tier`: HardwareTier reference
- `components`: array<HardwareComponent> - Specific components owned
- `cloud_setup`: CloudSetup reference - Cloud configuration if applicable
- `setup_date`: datetime - When configuration was established
- `validation_status`: enum - "pending" | "validated" | "failed"
- `limitations`: array<string> - Known limitations of current setup

### CloudSetup
**Purpose**: Manages cloud environment configurations

**Fields**:
- `id`: string - Unique identifier
- `student_id`: string - Student identifier
- `cloud_provider`: string - Cloud service provider
- `instance_type`: string - Cloud instance specification
- `region`: string - Geographic region
- `storage_configuration`: object - Storage setup details
- **estimated_monthly_cost**: number - Projected monthly cost
- `auto_shutdown`: boolean - Automatic shutdown configuration
- `last_accessed`: datetime - Last usage timestamp

## Content Management Entities

### Version
**Purpose**: Tracks content versions and compatibility

**Fields**:
- `id`: string - Unique version identifier
- `content_type`: enum - "module" | "chapter" | "code_example" | "assessment" | "lab_setup"
- `content_id`: string - Reference to content item
- `version_number`: string - Semantic version (e.g., "1.2.0")
- `hardware_compatibility`: array<HardwareTier> - Compatible hardware configurations
- `change_description`: string - What changed in this version
- `author`: string - Who made the change
- **change_date**: datetime - When change was made
- `migration_notes`: string - Notes for upgrading from previous versions

### Review
**Purpose**: Tracks content review and validation process

**Fields**:
- `id`: string - Unique review identifier
- `content_id`: string - Content being reviewed
- `reviewer_id`: string - Reviewer identifier
- `review_type`: enum - "technical" | "pedagogical" | "accessibility" | "hardware"
- `status`: enum - "pending" | "approved" | "needs_changes"
- `feedback`: text - Review feedback and suggestions
- `hardware_tested`: array<HardwareTier> - Hardware configurations tested
- `review_date`: datetime - Review completion date
- **approval_level**: enum - "draft" | "beta" | "production"

## State Transitions

### Module Lifecycle
1. **Draft** → **Review** (content ready for review)
2. **Review** → **Approved** (technical and pedagogical approval)
3. **Approved** → **Published** (content live on platform)
4. **Published** → **Update** (content revisions)
5. **Update** → **Published** (revisions approved and published)

### Student Progress States
1. **Not Started** → **In Progress** (student begins module/chapter)
2. **In Progress** → **Completed** (student finishes all assessments)
3. **Completed** → **Mastered** (student achieves high scores and practical skills)

### Hardware Configuration States
1. **Planning** → **Purchasing** (hardware selection and budgeting)
2. **Purchasing** → **Setup** (hardware acquisition)
3. **Setup** → **Validation** (installation and configuration)
4. **Validation** → **Active** (ready for educational use)
5. **Active** → **Upgrade** (hardware improvements or replacements)

## Data Relationships

```
Module (1) -----> (N) Chapter
Module (1) -----> (N) LearningObjective
Chapter (1) --> (N) LearningObjective
Chapter (1) --> (N) CodeExample
Chapter (1) --> (N) Assessment
Chapter (1) --> (1) HardwareRequirement
HardwareRequirement (1) --> (N) HardwareTier
HardwareTier (1) --> (N) BudgetItem
CloudAlternative (1) --> (1) HardwareRequirement
CapstoneProject (1) --> (N) Module
Student (1) --> (N) StudentProgress
Student (1) --> (1) HardwareConfiguration
HardwareConfiguration (1) --> (1) CloudSetup
LabInfrastructure (1) --> (N) SetupStep
```

## Performance Considerations

### Indexing Strategy
- Primary indexes on all `id` fields
- Composite indexes on frequently queried relationships (student_progress, hardware_compatibility)
- Full-text search indexes on content fields (titles, descriptions)
- Date-based indexes for tracking progress and versions
- Cost-based indexes for budget planning queries

### Caching Strategy
- Cache frequently accessed modules and chapters
- Cache student progress data for performance
- Cache hardware compatibility matrices
- Cache budget calculation results
- Cache cloud service pricing information

### Data Validation
- Referential integrity for all relationships
- Content format validation before storage
- Hardware compatibility validation before publishing
- Version compatibility checks during updates
- Budget calculation accuracy verification

This data model provides a comprehensive foundation for the Physical AI & Humanoid Robotics educational platform, supporting the complex requirements of hardware management, budget planning, and multi-tier accessibility while maintaining scalability and performance.