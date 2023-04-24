<template>
  <div>
    <h2>Zoomable Force Directed Graph</h2>
    <svg id="svg" width="1000" height="700" class="container-border" />
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, h, nextTick } from 'vue'
  import * as d3 from 'd3'
  var nodesData = [
    { name: 'Lillian', sex: 'F' },
    { name: 'Gordon', sex: 'M' },
    { name: 'Sylvester', sex: 'M' },
    { name: 'Mary', sex: 'F' },
    { name: 'Helen', sex: 'F' },
    { name: 'Jamie', sex: 'M' },
    { name: 'Jessie', sex: 'F' },
    { name: 'Ashton', sex: 'M' },
    { name: 'Duncan', sex: 'M' },
    { name: 'Evette', sex: 'F' },
    { name: 'Mauer', sex: 'M' },
    { name: 'Fray', sex: 'F' },
    { name: 'Duke', sex: 'M' },
    { name: 'Baron', sex: 'M' },
    { name: 'Infante', sex: 'M' },
    { name: 'Percy', sex: 'M' },
    { name: 'Cynthia', sex: 'F' },
    { name: 'Feyton', sex: 'M' },
    { name: 'Lesley', sex: 'F' },
    { name: 'Yvette', sex: 'F' },
    { name: 'Maria', sex: 'F' },
    { name: 'Lexy', sex: 'F' },
    { name: 'Peter', sex: 'M' },
    { name: 'Ashley', sex: 'F' },
    { name: 'Finkler', sex: 'M' },
    { name: 'Damo', sex: 'M' },
    { name: 'Imogen', sex: 'F' },
  ]
  // Sample links data
  // type: A for Ally, E for Enemy
  var linksData = [
    { source: 'Sylvester', target: 'Gordon', type: 'A' },
    { source: 'Sylvester', target: 'Lillian', type: 'A' },
    { source: 'Sylvester', target: 'Mary', type: 'A' },
    { source: 'Sylvester', target: 'Jamie', type: 'A' },
    { source: 'Sylvester', target: 'Jessie', type: 'A' },
    { source: 'Sylvester', target: 'Helen', type: 'A' },
    { source: 'Helen', target: 'Gordon', type: 'A' },
    { source: 'Mary', target: 'Lillian', type: 'A' },
    { source: 'Ashton', target: 'Mary', type: 'A' },
    { source: 'Duncan', target: 'Jamie', type: 'A' },
    { source: 'Gordon', target: 'Jessie', type: 'A' },
    { source: 'Sylvester', target: 'Fray', type: 'E' },
    { source: 'Fray', target: 'Mauer', type: 'A' },
    { source: 'Fray', target: 'Cynthia', type: 'A' },
    { source: 'Fray', target: 'Percy', type: 'A' },
    { source: 'Percy', target: 'Cynthia', type: 'A' },
    { source: 'Infante', target: 'Duke', type: 'A' },
    { source: 'Duke', target: 'Gordon', type: 'A' },
    { source: 'Duke', target: 'Sylvester', type: 'A' },
    { source: 'Baron', target: 'Duke', type: 'A' },
    { source: 'Baron', target: 'Sylvester', type: 'E' },
    { source: 'Evette', target: 'Sylvester', type: 'E' },
    { source: 'Cynthia', target: 'Sylvester', type: 'E' },
    { source: 'Cynthia', target: 'Jamie', type: 'E' },
    { source: 'Mauer', target: 'Jessie', type: 'E' },
    { source: 'Duke', target: 'Lexy', type: 'A' },
    { source: 'Feyton', target: 'Lexy', type: 'A' },
    { source: 'Maria', target: 'Feyton', type: 'A' },
    { source: 'Baron', target: 'Yvette', type: 'E' },
    { source: 'Evette', target: 'Maria', type: 'E' },
    { source: 'Cynthia', target: 'Yvette', type: 'E' },
    { source: 'Maria', target: 'Jamie', type: 'E' },
    { source: 'Maria', target: 'Lesley', type: 'E' },
    { source: 'Ashley', target: 'Damo', type: 'A' },
    { source: 'Damo', target: 'Lexy', type: 'A' },
    { source: 'Maria', target: 'Feyton', type: 'A' },
    { source: 'Finkler', target: 'Ashley', type: 'E' },
    { source: 'Sylvester', target: 'Maria', type: 'E' },
    { source: 'Peter', target: 'Finkler', type: 'E' },
    { source: 'Ashley', target: 'Gordon', type: 'E' },
    { source: 'Maria', target: 'Imogen', type: 'E' },
  ]

  function init() {
    // create somewhere to put the force directed graph
    let svg = d3.select('#svg')
    let width = +svg.attr('width')
    let height = +svg.attr('height')
    let radius = 15
    // set up the simulation and add forces
    let simulation = d3.forceSimulation().nodes(nodesData)
    let linkForce = d3.forceLink(linksData).id(function (d) {
      return d.name
    })
    let chargeForce = d3.forceManyBody().strength(-100)
    let centerForce = d3.forceCenter(width / 2, height / 2)
    simulation
      .force('chargeForce', chargeForce)
      .force('centerForce', centerForce)
      .force('links', linkForce)
    // add tick instructions:
    simulation.on('tick', tickActions)
    // add encompassing group for the zoom
    let g = svg.append('g').attr('class', 'everything')
    // draw lines for the links
    let link = g
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(linksData)
      .enter()
      .append('line')
      .attr('stroke-width', 2)
      .style('stroke', linkColour)
    // draw circles for the nodes
    let node = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(nodesData)
      .enter()
      .append('circle')
      .attr('r', radius)
      .attr('fill', circleColour)
    let dragHandler = d3.drag().on('start', dragStart).on('drag', dragDrag).on('end', dragEnd)
    dragHandler(node)
    // add zoom capabilities
    let zoomHandler = d3.zoom().on('zoom', zoomActions)
    zoomHandler(svg)
    /** Functions **/
    // Function to choose what color circle we have
    // Let's return blue for males and red for females
    function circleColour(d) {
      if (d.sex === 'M') {
        return 'blue'
      } else if (d.sex === 'S') {
        return 'red'
      } else {
        return 'pink'
      }
    }
    // Function to choose the line colour and thickness
    // If the link type is 'A' return green
    // If the link type is 'E' return red
    function linkColour(d) {
      if (d.type === 'A') {
        return 'green'
      } else {
        return 'red'
      }
    }
    // Drag functions
    // d is the node
    function dragStart(event) {
      if (!event.active) simulation.alphaTarget(0.1).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    }
    // make sure you can't drag the circle outside the box
    function dragDrag(event) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    }
    function dragEnd(event) {
      if (!event.active) simulation.alphaTarget(0.1)
      event.subject.fx = event.x
      event.subject.fy = event.y
    }
    // Zoom functions
    function zoomActions(event) {
      g.attr('transform', event.transform)
    }
    function tickActions() {
      // update circle positions each tick of the simulation
      node
        .attr('cx', function (d) {
          return d.x
        })
        .attr('cy', function (d) {
          return d.y
        })
      // update link positions
      link
        .attr('x1', function (d) {
          return d.source.x
        })
        .attr('y1', function (d) {
          return d.source.y
        })
        .attr('x2', function (d) {
          return d.target.x
        })
        .attr('y2', function (d) {
          return d.target.y
        })
    }
  }
  onMounted(() => {
    setTimeout(() => {
      console.log(nodesData)
      nodesData = [...nodesData, { name: 'AAA', sex: 'S' }, { name: 'BBB', sex: 'S' }]
      linksData = [
        ...linksData,
        {
          source: 'AAA',
          target: 'Lillian',
          type: 'E',
        },
        {
          source: 'BBB',
          target: 'Lillian',
          type: 'E',
        },
      ]
      d3.select('#svg').selectAll('*').remove()
      init()
    }, 4000)
  })
  onMounted(init)
</script>

<style lang="scss" scoped></style>
