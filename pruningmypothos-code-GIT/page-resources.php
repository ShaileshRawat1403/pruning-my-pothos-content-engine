<?php
/* Template Name: Resources */

// ✅ JSON-LD Schema for Resources Page
$resources_schema = [
  "@context" => "https://schema.org",
  "@type" => "CollectionPage",
  "name" => "Curated Resources | Pruning My Pothos",
  "description" => "Explore curated tools, guides, and frameworks to rethink content, tech, and transformation. Designed for writers, change enablers, and lifelong learners.",
  "url" => home_url('/resources/'),
  "inLanguage" => "en",
  "publisher" => [
    "@type" => "Organization",
    "name" => "PruningMyPothos",
    "url" => home_url(),
    "logo" => [
      "@type" => "ImageObject",
      "url" => "https://pruningmypothos.com/wp-content/uploads/2025/06/logo-pruning-my-pothos.png",
      "width" => 512,
      "height" => 512
    ]
  ],
  "mainEntity" => [
    "@type" => "ItemList",
    "name" => "Resource Categories",
    "itemListElement" => [
      [
        "@type" => "SiteNavigationElement",
        "name" => "Code & Craft",
        "url" => home_url('/resources/code-and-craft/')
      ],
      [
        "@type" => "SiteNavigationElement",
        "name" => "Strategy & Systems",
        "url" => home_url('/resources/strategy-and-systems/')
      ],
      [
        "@type" => "SiteNavigationElement",
        "name" => "Reflection & Growth",
        "url" => home_url('/resources/reflection-and-growth/')
      ],
      [
        "@type" => "SiteNavigationElement",
        "name" => "Learning Loops",
        "url" => home_url('/resources/learning-loops/')
      ]
    ]
  ]
];

// Inject schema into footer
add_action('wp_footer', function () use ($resources_schema) {
  echo '<script type="application/ld+json">' . json_encode($resources_schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . '</script>';
});

get_header(); 
?>

<!-- Hero Section -->
<div class="hero-section fade-in">
  <h1>Explore Our Curated Resources</h1>
  <p>Browse our collection of articles, guides, tools, and more, designed to inspire personal growth, mindfulness, and reflection.</p>
  <a href="#resources-grid" class="cta-btn">Start Exploring</a>
</div>

<!-- Category Section moved just below hero -->
<div class="resource-categories fade-in">
  <h2>Browse The Stack</h2>
<ul>
  <li>
    <a href="/resources/code-and-craft/" 
       title="You don’t need to code to make things make sense.">
       Code & Craft
    </a>
  </li>
  <li>
    <a href="/resources/strategy-and-systems/" 
       title="Most systems fail because no one explains how they work.">
       Strategy & Systems
    </a>
  </li>
  <li>
    <a href="/resources/reflection-and-growth/" 
       title="If your process and progress feels heavy, maybe it’s trying to tell you something.">
       Reflection & Growth
    </a>
  </li>
  <li>
    <a href="/resources/learning-loops/" 
       title="Some lessons don’t teach. They just wait to be learned.">
       Learning Loops
    </a>
  </li>
</ul>
</div>

<!-- Featured Resources -->
<div class="featured-resources fade-in">
  <h2>Featured Resources</h2>
  <div class="featured-resource-grid">

    <!-- Git for Writers -->
    <div class="featured-resource-card">
      <img src="<?php echo get_template_directory_uri(); ?>/images/resources/git-for-writers.jpg" alt="Git for Writers" loading="lazy">
      <h3>Git for Writers</h3>
      <p>Version control for the version-confused.</p>
      <a href="https://github.com/ShaileshRawat1403/sans_serif_sentiments/blob/main/README.md" target="_blank" class="resource-btn">Explore Now</a>
    </div>

    <!-- Markdown 101 -->
    <div class="featured-resource-card">
      <img src="<?php echo get_template_directory_uri(); ?>/images/resources/markdown-101.jpg" alt="Markdown 101" loading="lazy">
      <h3>Markdown 101</h3>
      <p>From headlines to hashes—Markdown made human.</p>
      <a href="https://www.markdownguide.org/basic-syntax/" target="_blank" class="resource-btn">Read Guide</a>
    </div>
    
<!-- Why Your Prompt Didn’t Work -->
<div class="featured-resource-card">
  <img 
    src="https://pruningmypothos.com/wp-content/uploads/2025/06/why-your-prompt-didnt-work-square-card.png" 
    alt="Minimalist graphic with a terminal interface above the text 'Why Your Prompt Didn’t Work' — a visual guide to prompt troubleshooting and AI communication clarity" 
    loading="lazy"
  >
  <h3>Why Your Prompt Didn’t Work</h3>
  <p>Fixing broken prompts by fixing broken thinking.</p>
  <a 
    href="https://github.com/ShaileshRawat1403/sans_serif_sentiments/blob/main/ai-handbook/why-your-prompt-didnt-work.md" 
    target="_blank" 
    class="resource-btn"
  >
    Open Guide
  </a>
</div>
    
    <!-- AI Handbook -->
<div class="featured-resource-card">
  <img src="<?php echo get_template_directory_uri(); ?>/images/resources/ai-handbook.jpg" alt="AI Handbook by Shailesh Rawat" loading="lazy">
  <h3>AI Handbook</h3>
  <p>A practical guide to prompts, patterns, and perception in the age of intelligence.</p>
  <a href="https://github.com/ShaileshRawat1403/sans_serif_sentiments/tree/main/ai-handbook" target="_blank" class="resource-btn">Explore Guide</a>
</div>

    <!-- HBR: Change Management -->
    <div class="featured-resource-card">
      <img src="<?php echo get_template_directory_uri(); ?>/images/resources/change-management-hbr.jpg" alt="Change Management HBR" loading="lazy">
      <h3>Change Management Communication</h3>
      <p>Mastering the messaging that moves people.</p>
      <a href="https://hbr.org/2022/04/change-is-hard-heres-how-to-make-it-less-painful" target="_blank" class="resource-btn">Read Article</a>
    </div>

    <!-- McKinsey: Transformation -->
    <div class="featured-resource-card">
      <img src="<?php echo get_template_directory_uri(); ?>/images/resources/mckinsey-transformation.jpg" alt="McKinsey Transformation" loading="lazy">
      <h3>Science of Transformation</h3>
      <p>When strategy meets structure, success isn’t accidental.</p>
      <a href="https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/the-science-of-organizational-transformations" target="_blank" class="resource-btn">Explore Insight</a>
    </div>

    <!-- Pothos: The Plant, The Path -->
    <div class="featured-resource-card">
      <img src="<?php echo get_template_directory_uri(); ?>/images/resources/pothos-plant-path.jpg" alt="Pothos: The Plant, The Path" loading="lazy">
      <h3>Pothos: The Plant, The Path</h3>
      <p>A houseplant’s guide to desire, detachment, and design.</p>
      <a href="/blog/pothos-the-plant-the-path/" class="resource-btn">Read Blog</a>
    </div>

    <!-- Learn Git Branching -->
    <div class="featured-resource-card">
      <img src="<?php echo get_template_directory_uri(); ?>/images/resources/learn-git-branching.jpg" alt="Learn Git Branching" loading="lazy">
      <h3>Learn Git Branching</h3>
      <p>Visually understand how Git works—branch by branch.</p>
      <a href="https://learngitbranching.js.org/" target="_blank" class="resource-btn">Start Learning</a>
    </div>

    <!-- Sticky Notes Springboard -->
    <div class="featured-resource-card">
      <img src="<?php echo get_template_directory_uri(); ?>/images/resources/sticky-notes-springboard-for-a-shitty-life.jpg" alt="Sticky Notes Springboard" loading="lazy">
      <h3>Sticky Notes Springboard</h3>
      <p>How 3-inch squares can change your mental architecture.</p>
      <a href="/blog/sticky-notes-springboard/" class="resource-btn">Read Blog</a>
    </div>

    <!-- Sans Serif Sentiments (GitHub Repo) -->
    <div class="featured-resource-card">
      <img src="<?php echo get_template_directory_uri(); ?>/images/resources/sans-serif-sentiments.jpg" alt="Sans Serif Sentiments GitHub" loading="lazy">
      <h3>Sans Serif Sentiments</h3>
      <p>Version-controlled insights, guides, and frameworks.</p>
      <a href="https://github.com/ShaileshRawat1403/sans_serif_sentiments" target="_blank" class="resource-btn">View Repo</a>
    </div>

  </div>
</div>

<!-- Search Section moved just before footer -->
<div class="resource-search fade-in">
  <input type="text" placeholder="Search for resources..." aria-label="Search resources">
  <button>Search</button>
</div>

<?php 
get_footer(); 
?>
