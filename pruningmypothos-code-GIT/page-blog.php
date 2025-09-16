<?php
/**
 * Template Name: Blog Page
 */

$breadcrumbs = [
  [
    "@type" => "ListItem",
    "position" => 1,
    "name" => "Home",
    "item" => home_url()
  ],
  [
    "@type" => "ListItem",
    "position" => 2,
    "name" => "Blog",
    "item" => home_url('/blog/')
  ]
];

$schema_data = [
  "@context" => "https://schema.org",
  "@type" => "CollectionPage",
  "name" => "Blog - Pruning My Pothos",
  "description" => "Insightful articles on AI, tech transformation, slow growth, systems and sentences, change translation, and exploring life. Read, reflect, and rethink how change really happens.",
  "url" => home_url('/blog/'),
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
  "breadcrumb" => [
    "@type" => "BreadcrumbList",
    "itemListElement" => $breadcrumbs
  ]
];
?>

<script type="application/ld+json">
  <?php echo json_encode($schema_data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE); ?>
</script>

<?php get_header(); ?>

<main class="blog-page container">

  <!-- Breadcrumbs -->
  <nav class="breadcrumbs fade-in">
    <a href="<?php echo home_url(); ?>">Home</a> &gt;
    <span>Blog</span>
  </nav>

  <!-- Hero Section -->
  <section class="hero-section fade-in">
    <h1>The Blog</h1>
    <p>Reflections from Personal, Professional, and Philosophical Perspectives.</p>
  </section>

<!-- Category Filters -->
<section class="blog-category-grid fade-in" style="margin-top: 80px;">
  <h2>Browse by Category</h2>
  <div class="category-card-grid">

    <a href="<?php echo esc_url( get_category_link( get_cat_ID( 'Sticky Notes Springboard' ) ) ); ?>" class="category-card">
      <div class="icon">📝</div>
      <h3>Sticky Notes</h3>
      <p>Quick sparks of thought and inspiration.</p>
    </a>

    <a href="<?php echo esc_url( get_category_link( get_cat_ID( 'Echoes & Ethos' ) ) ); ?>" class="category-card">
      <div class="icon">🎧</div>
      <h3>Echoes & Ethos</h3>
      <p>Reflections on values, self and depth.</p>
    </a>

    <a href="<?php echo esc_url( get_category_link( get_cat_ID( 'Terms & Conditions' ) ) ); ?>" class="category-card">
      <div class="icon">📜</div>
      <h3>Terms & Conditions</h3>
      <p>Framing systems and philosophy of structure.</p>
    </a>

  </div>
</section>

<!--
<section class="filter-tags fade-in">
  ...
</section>
-->

  <!-- Blog Posts Grid -->
  <section class="blog-grid fade-in">

    <?php
    $paged = ( get_query_var( 'paged' ) ) ? get_query_var( 'paged' ) : 1;

    $args = array(
      'post_type'      => 'post',
      'posts_per_page' => 9,
      'paged'          => $paged
    );

    $blog_query = new WP_Query( $args );

    if ( $blog_query->have_posts() ) :
      while ( $blog_query->have_posts() ) : $blog_query->the_post(); ?>

        <article class="post-card fade-in">

          <?php if ( has_post_thumbnail() ) : ?>
            <a href="<?php the_permalink(); ?>">
              <?php the_post_thumbnail( 'medium', [
                'loading' => 'lazy',
                'alt'     => get_the_title()
              ] ); ?>
            </a>
          <?php endif; ?>

          <div class="post-content">
            <span class="post-category">
              <?php
              $categories = get_the_category();
              if ( ! empty( $categories ) ) {
                echo esc_html( $categories[0]->name );
              }
              ?>
            </span>

            <h2 class="post-title">
              <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
            </h2>

            <p class="post-excerpt"><?php echo wp_trim_words( get_the_excerpt(), 20 ); ?></p>

            <a href="<?php the_permalink(); ?>" class="cta-btn">Read More</a>
          </div>

        </article>

      <?php endwhile; ?>

      <!-- Pagination -->
      <div class="pagination fade-in" aria-label="Blog page navigation">
        <?php
        echo paginate_links( array(
          'total'     => $blog_query->max_num_pages,
          'prev_text' => '&laquo;',
          'next_text' => '&raquo;',
        ) );
        ?>
      </div>

    <?php else : ?>
      <p>No posts found.</p>
    <?php endif; ?>

    <?php wp_reset_postdata(); ?>

  </section>

</main>

<?php get_footer(); ?>
