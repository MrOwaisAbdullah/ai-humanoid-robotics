/sp.specify
Generate the complete educational content for the "Physical AI & Humanoid Robotics" textbook.

**Context & Goals:**
This is Module 2. We need to fill the Docusaurus skeleton with high-quality, technical content based on the provided course curriculum. The content must be authoritative, structured, and optimized for an AI-driven learning experience.

**Source Material:**
Refer to `course_details.md` for the exact curriculum, weekly breakdown, and learning outcomes.

**Requirements:**

1.  **Content Structure (12 Chapters)**:
    *   **Part 1: Foundations (Weeks 1-2)**
        *   Chapter 1: Introduction to Physical AI & Embodied Intelligence.
        *   Chapter 2: Sensors & Perception (LiDAR, Cameras, IMUs).
    *   **Part 2: The Nervous System (Weeks 3-5)**
        *   Chapter 3: ROS 2 Architecture & Core Concepts.
        *   Chapter 4: Building ROS 2 Nodes with Python.
        *   Chapter 5: Launch Systems & Parameter Management.
    *   **Part 3: The Digital Twin (Weeks 6-7)**
        *   Chapter 6: Simulation with Gazebo (URDF/SDF).
        *   Chapter 7: Physics Simulation & Unity Integration.
    *   **Part 4: The AI Brain (Weeks 8-10)**
        *   Chapter 8: NVIDIA Isaac Sim & SDK.
        *   Chapter 9: Visual SLAM & Navigation (Nav2).
        *   Chapter 10: Reinforcement Learning for Control.
    *   **Part 5: Advanced Humanoids (Weeks 11-13)**
        *   Chapter 11: Humanoid Kinematics & Bipedal Locomotion.
        *   Chapter 12: VLA (Vision-Language-Action) & Conversational Robotics.
2.  **Chapter Format**:
    *   **Title & Metadata**: Clear frontmatter (slug, title, description, tags).
    *   **Learning Objectives**: Bullet points at the start.
    *   **Body Content**: 2000+ words per chapter (approximate target, but focus on quality/completeness).
    *   **Code Blocks**: Python/C++ examples for ROS 2, Config snippets (YAML/XML) for URDF/Launch files.
    *   **Diagrams**: Use Mermaid.js code blocks for architecture diagrams (ROS graphs, state machines).
    *   **Assessment**: A "Knowledge Check" section at the end of each chapter.
3.  **Style**:
    *   Technical but accessible.
    *   "AI-Native": Written to be easily parsed by RAG (clear headers, semantic structure).

**Deliverable:**
- 12 Markdown/MDX files in the `docs/` directory, correctly organized in subfolders.
- `sidebars.js` updated to reflect the chapter hierarchy.
