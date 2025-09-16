<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
  <meta charset="<?php bloginfo('charset'); ?>">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- Google Fonts: Space Grotesk + Manrope -->
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600&display=swap" rel="stylesheet">

  <!-- ✅ SEO META TAGS -->
  <title>PruningMyPothos | Rethinking Growth, Tech & Transformation</title>
  <meta name="description" content="For thinkers, writers, and change agents. Navigate AI, slow growth, content enablement, and change management.">
  <meta name="keywords" content="change management, slow growth, digital transformation, personal growth, artificial intelligence, mindful tech, existentialism, tech for writers, AI learning, machine learning, prompt engineering, prompt design, learn AI, ChatGPT, Gemini AI, Claude AI, Perplexity, learn GitHub, learn Confluence, content enablement, pruningmypothos, pothos philosophy, modern stoicism, self-learning strategy, career development, poeticmayhem">
  <link rel="canonical" href="https://pruningmypothos.com/" />
  
  <!-- ✅ JSON-LD Schema Markup -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "PruningMyPothos",
  "url": "https://pruningmypothos.com",
  "description": "A mindful space exploring technology, transformation, content enablement, and existential growth. Created by PoeticMayhem, for thinkers, writers, and change agents navigating AI and personal meaning.",
  "inLanguage": "en",
  "publisher": {
    "@type": "Organization",
    "name": "PruningMyPothos",
    "url": "https://pruningmypothos.com",
    "logo": {
      "@type": "ImageObject",
      "url": "https://pruningmypothos.com/wp-content/uploads/2025/06/logo-pruning-my-pothos.png",
      "width": 512,
      "height": 512
    }
  },
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://pruningmypothos.com/?s={search_term_string}",
    "query-input": "required name=search_term_string"
  },
  "keywords": [
    "change management",
    "content enablement",
    "tech transformation",
    "digital transformation",
    "artificial intelligence",
    "existentialism",
    "mindful tech",
    "personal growth",
    "slow growth",
    "philosophy and technology",
    "pruningmypothos",
    "pothos philosophy"
  ]
}
</script>

  <?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>

<header class="boho-header" role="banner">
  <div class="header-container">

    <!-- Site Logo -->
    <div class="header-logo">
<a href="<?php echo home_url(); ?>">Pruning<em>My</em>Pothos</a>
    </div>

    <!-- Mobile Menu Toggle -->
    <button 
      class="menu-toggle" 
      aria-label="Toggle Navigation" 
      aria-expanded="false"
      aria-controls="primary-menu"
    >☰</button>

    <!-- Navigation Menu -->
    <nav class="header-nav-container" role="navigation" aria-label="Primary Navigation">
      <ul class="header-nav" id="primary-menu">
        <li><a href="<?php echo home_url(); ?>">Home</a></li>
        <li><a href="<?php echo home_url('/about'); ?>">About</a></li>
        <li><a href="<?php echo home_url('/blog'); ?>">Blog</a></li>
        <li><a href="<?php echo home_url('/gallery'); ?>">Gallery</a></li> <!-- ✅ Added -->
        <li><a href="<?php echo home_url('/resources'); ?>">Resources</a></li>
        <li><a href="<?php echo home_url('/the-antithesis'); ?>">The Antithesis</a></li> <!-- ✅ Added -->
        <li><a href="<?php echo home_url('/contact'); ?>">Contact</a></li>
      </ul>
    </nav>

    <!-- Dark Mode Toggle (separated from nav links) -->
    <button id="darkModeToggle" aria-label="Toggle Dark Mode">🌓</button>

  </div>
</header>
