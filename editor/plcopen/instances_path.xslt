<?xml version="1.0"?>
<xsl:stylesheet xmlns:exsl="http://exslt.org/common" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:ppx="http://www.plcopen.org/xml/tc6_0201" xmlns:ns="beremiz" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" extension-element-prefixes="ns" version="1.0" exclude-result-prefixes="ns">
  <xsl:output method="xml"/>
  <xsl:param name="instance_type"/>
  <xsl:template match="text()"/>
  <xsl:variable name="project" select="ns:GetProject()"/>
  <xsl:variable name="stdlib" select="ns:GetStdLibs()"/>
  <xsl:variable name="extensions" select="ns:GetExtensions()"/>
  <xsl:variable name="all_types" select="($project | $stdlib | $extensions)/ppx:types"/>
  <xsl:template match="ppx:project">
    <xsl:apply-templates select="ppx:instances/ppx:configurations/ppx:configuration"/>
  </xsl:template>
  <xsl:template match="ppx:configuration">
    <xsl:apply-templates select="ppx:globalVars/ppx:variable[ppx:type/ppx:derived] | ppx:resource">
      <xsl:with-param name="parent_path">
        <xsl:value-of select="@name"/>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="ppx:resource">
    <xsl:param name="parent_path"/>
    <xsl:variable name="resource_path">
      <xsl:value-of select="$parent_path"/>
      <xsl:text>.</xsl:text>
      <xsl:value-of select="@name"/>
    </xsl:variable>
    <xsl:apply-templates select="ppx:globalVars/ppx:variable[ppx:type/ppx:derived] | ppx:pouInstance | ppx:task/ppx:pouInstance">
      <xsl:with-param name="parent_path">
        <xsl:value-of select="$resource_path"/>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="ppx:pouInstance">
    <xsl:param name="parent_path"/>
    <xsl:variable name="pou_instance_path">
      <xsl:value-of select="$parent_path"/>
      <xsl:text>.</xsl:text>
      <xsl:value-of select="@name"/>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="@typeName=$instance_type">
        <xsl:value-of select="ns:AddInstance($pou_instance_path)"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="type_name">
          <xsl:value-of select="@typeName"/>
        </xsl:variable>
        <xsl:apply-templates select="$all_types/ppx:pous/ppx:pou[@name=$type_name] |                          $all_types/ppx:dataTypes/ppx:dataType[@name=$type_name]">
          <xsl:with-param name="instance_path">
            <xsl:value-of select="$pou_instance_path"/>
          </xsl:with-param>
        </xsl:apply-templates>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="ppx:pou">
    <xsl:param name="instance_path"/>
    <xsl:apply-templates select="ppx:interface/*/ppx:variable[ppx:type/ppx:derived]">
      <xsl:with-param name="parent_path">
        <xsl:value-of select="$instance_path"/>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="ppx:dataType">
    <xsl:param name="instance_path"/>
    <xsl:apply-templates select="ppx:baseType/*[self::ppx:derived or self::ppx:struct or self::ppx:array]">
      <xsl:with-param name="parent_path">
        <xsl:value-of select="$instance_path"/>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="ppx:variable">
    <xsl:param name="parent_path"/>
    <xsl:variable name="variable_path">
      <xsl:value-of select="$parent_path"/>
      <xsl:text>.</xsl:text>
      <xsl:value-of select="@name"/>
    </xsl:variable>
    <xsl:apply-templates select="ppx:type/ppx:derived">
      <xsl:with-param name="variable_path">
        <xsl:value-of select="$variable_path"/>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="ppx:derived">
    <xsl:param name="variable_path"/>
    <xsl:choose>
      <xsl:when test="@name=$instance_type">
        <xsl:value-of select="ns:AddInstance($variable_path)"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="type_name">
          <xsl:value-of select="@name"/>
        </xsl:variable>
        <xsl:apply-templates select="$all_types/ppx:pous/ppx:pou[@name=$type_name] |                          $all_types/ppx:dataTypes/ppx:dataType[@name=$type_name]">
          <xsl:with-param name="instance_path">
            <xsl:value-of select="$variable_path"/>
          </xsl:with-param>
        </xsl:apply-templates>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="ppx:struct">
    <xsl:param name="variable_path"/>
    <xsl:for-each select="ppx:variable[ppx:type/ppx:derived or ppx:type/ppx:struct or ppx:type/ppx:array]">
      <xsl:variable name="element_path">
        <xsl:value-of select="$variable_path"/>
        <xsl:text>.</xsl:text>
        <xsl:value-of select="@name"/>
      </xsl:variable>
    </xsl:for-each>
    <xsl:apply-templates select="ppx:type/*[self::ppx:derived or self::ppx:struct or self::ppx:array]">
      <xsl:with-param name="variable_path">
        <xsl:value-of select="$element_path"/>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>
  <xsl:template match="ppx:array">
    <xsl:param name="variable_path"/>
    <xsl:apply-templates select="ppx:baseType/*[self::ppx:derived or self::ppx:struct or self::ppx:array]">
      <xsl:with-param name="variable_path">
        <xsl:value-of select="$variable_path"/>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>
</xsl:stylesheet>
