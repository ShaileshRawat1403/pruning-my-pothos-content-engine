<?php
// Generate breadcrumb schema items dynamically (optional)
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
  ],
  [
    "@type" => "ListItem",
    "position" => 3,
    "name" => single_cat_title('', false),
    "item" => get_category_link(get_queried_object_id())
  ]
];

$schema_data = [
  "@context" => "https://schema.org",
  "@type" => "CollectionPage",
  "name" => single_cat_title('', false),
  "description" => strip_tags(category_description()),
  "url" => get_category_link(get_queried_object_id()),
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

<main class="category-page container">

  <!-- Breadcrumbs -->
  <nav class="breadcrumbs">
    <a href="<?php echo home_url(); ?>">Home</a> &gt;
    <a href="<?php echo home_url('/blog'); ?>">Blog</a> &gt;
    <span><?php single_cat_title(); ?></span>
  </nav>

  <!-- Hero Section -->
  <section class="hero-section">
    <h1><?php single_cat_title(); ?></h1>
    <?php if (category_description()) : ?>
      <p class="category-description">
        <?php echo category_description(); ?>
      </p>
    <?php endif; ?>
  </section>

  <!-- Main Content + Sidebar Layout -->
  <div class="content-sidebar-wrapper">

    <!-- Main Blog Content -->
    <div class="main-content">

      <!-- Filter Tags Section -->
      <section class="filter-tags">
        <h3>Filter by Tag</h3>
        <ul class="tag-list">
          <?php
          $tags = get_tags();
          if ($tags) :
            foreach ($tags as $tag) : ?>
              <li>
                <a href="<?php echo get_tag_link($tag->term_id); ?>">
                  <?php echo $tag->name; ?>
                </a>
              </li>
            <?php endforeach; ?>
          <?php else : ?>
            <li>No tags found.</li>
          <?php endif; ?>
        </ul>
      </section>

      <!-- Blog Posts Grid -->
      <section class="blog-grid">

        <?php if (have_posts()) : ?>
          <?php while (have_posts()) : the_post(); ?>

            <article class="post-card">

              <?php if (has_post_thumbnail()) : ?>
                <a href="<?php the_permalink(); ?>">
                  <?php the_post_thumbnail('medium', ['loading' => 'lazy']); ?>
                </a>
              <?php endif; ?>

              <div class="post-content">
                <span class="post-category">
                  <?php
                  $categories = get_the_category();
                  if (!empty($categories)) {
                    echo esc_html($categories[0]->name);
                  }
                  ?>
                </span>

                <h2 class="post-title">
                  <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
                </h2>

                <p class="post-excerpt">
                  <?php echo wp_trim_words(get_the_excerpt(), 20); ?>
                </p>

                <a href="<?php the_permalink(); ?>" class="cta-btn">Read More</a>
              </div>

            </article>

          <?php endwhile; ?>

          <!-- Pagination -->
          <div class="pagination">
            <?php
            echo paginate_links(array(
              'prev_text' => '&laquo;',
              'next_text' => '&raquo;',
            ));
            ?>
          </div>

        <?php else : ?>
          <p>No posts found in this category.</p>
        <?php endif; ?>

      </section><!-- .blog-grid -->

    </div><!-- .main-content -->

    <!-- Sidebar Widgets -->
    <aside class="sidebar">

      <!-- Search Widget -->
      <div class="widget search-widget">
        <?php get_search_form(); ?>
      </div>

      <!-- Recent Posts Widget -->
      <div class="widget recent-posts-widget">
        <h3>Recent Posts</h3>
        <ul>
          <?php
          $recent_posts = wp_get_recent_posts(['numberposts' => 5]);
          foreach ($recent_posts as $post) : ?>
            <li>
              <a href="<?php echo get_permalink($post['ID']); ?>">
                <?php echo esc_html($post['post_title']); ?>
              </a>
            </li>
          <?php endforeach; ?>
        </ul>
      </div>

      <!-- Categories Widget -->
      <div class="widget categories-widget">
        <h3>Categories</h3>
        <ul>
          <?php
          wp_list_categories([
            'orderby' => 'name',
            'title_li' => ''
          ]);
          ?>
        </ul>
      </div>

      <!-- Tags Widget -->
      <div class="widget tags-widget">
        <h3>Tags</h3>
        <div class="tag-cloud">
          <?php wp_tag_cloud(); ?>
        </div>
      </div>

    </aside><!-- .sidebar -->

  </div><!-- .content-sidebar-wrapper -->

</main>

<?php get_footer(); ?>
